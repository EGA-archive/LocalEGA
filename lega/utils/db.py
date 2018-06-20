# -*- coding: utf-8 -*-

'''
Database Connection
'''

import sys
import traceback
from functools import wraps
import logging
import psycopg2
from socket import gethostname
from time import sleep
import asyncio
import aiopg
from enum import Enum

from legacryptor import exceptions as crypt_exc

from ..conf import CONF
from .exceptions import FromUser, KeyserverError, PGPKeyError
from .amqp import publish, get_connection

LOG = logging.getLogger(__name__)

class Status(Enum):
    Received = 'Received'
    In_Progress = 'In progress'
    Completed = 'Completed'
    Archived = 'Archived'
    Error = 'Error'

######################################
##         DB connection            ##
######################################
def fetch_args(d):
    """Initializing a connection to db."""
    db_args = { 'user'     : d.get_value('postgres', 'user'),
                'password' : d.get_value('postgres', 'password'),
                'database' : d.get_value('postgres', 'db'),
                'host'     : d.get_value('postgres', 'host'),
                'port'     : d.get_value('postgres', 'port', conv=int)
    }
    LOG.info(f"Initializing a connection to: {db_args['host']}:{db_args['port']}/{db_args['database']}")
    return db_args

async def _retry(run, on_failure=None, exception=psycopg2.OperationalError):
    '''Main retry loop'''
    nb_try = CONF.get_value('postgres', 'try', conv=int, default=1)
    try_interval = CONF.get_value('postgres', 'try_interval', conv=int, default=1)
    LOG.debug(f"{nb_try} attempts (every {try_interval} seconds)")
    count = 0
    backoff = try_interval
    while count < nb_try:
        try:
            return await run()
        except exception as e:
            LOG.debug(f"Database connection error: {e!r}")
            LOG.debug(f"Retrying in {backoff} seconds")
            sleep( backoff )
            count += 1
            backoff = (2 ** (count // 10)) * try_interval
            # from  0 to  9, sleep 1 * try_interval secs
            # from 10 to 19, sleep 2 * try_interval secs
            # from 20 to 29, sleep 4 * try_interval secs ... etc

    # fail to connect
    if nb_try:
        LOG.error(f"Database connection fail after {nb_try} attempts ...")
    else:
        LOG.error("Database connection attempts was set to 0 ...")

    if on_failure:
        on_failure()


def retry_loop(on_failure=None, exception=psycopg2.OperationalError):
    '''Decorator retry something ``try`` times every ``try_interval`` seconds.
    Run the ``on_failure`` if after ``try`` attempts (configured in CONF).
    '''
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async def _process():
                    return await func(*args,**kwargs)
                return await _retry(_process, on_failure=on_failure, exception=exception)
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                async def _process():
                    return func(*args,**kwargs)
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_retry(_process, on_failure=on_failure, exception=exception))
        return wrapper
    return decorator

def _do_exit():
    LOG.error("Could not connect to the database: Exiting")
    sys.exit(1)

######################################
##         "Classic" code           ##
######################################
_conn = None
def cache_connection(func):
    '''Decorator to cache the database connection'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _conn
        if _conn is None or _conn.closed:
            _conn = func(*args, **kwargs)
        return _conn
    return wrapper

@cache_connection
@retry_loop(on_failure=_do_exit)
def connect():
    '''Get the database connection (which encapsulates a database session)

    Upon success, the connection is cached.

    Before success, we try to connect ``try`` times every ``try_interval`` seconds (defined in CONF)
    '''
    db_args = fetch_args(CONF)
    return psycopg2.connect(**db_args)


def insert_file(filename, user_id, stable_id):
    """Store file related information such as related ``user_id``, ``stable_id``, ``status`` etc."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT insert_file(%(filename)s,%(user_id)s,%(stable_id)s,%(status)s);',
                        { 'filename': filename, 'user_id': user_id, 'status' : Status.Received.value, 'stable_id': stable_id })
            file_id = (cur.fetchone())[0]
            if file_id:
                LOG.debug(f'Created id {file_id} for {filename}')
                return file_id
            else:
                raise Exception('Database issue with insert_file')


def get_errors(from_user=False):
    """Retrieve error from database."""
    query = 'SELECT * from errors WHERE from_user = true;' if from_user else 'SELECT * from errors;'
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

def set_error(file_id, error, from_user=False):
    """Store error related to ``file_id`` in database."""
    assert file_id, 'Eh? No file_id?'
    assert error, 'Eh? No error?'
    LOG.debug(f'Setting error for {file_id}: {error!s} | Cause: {error.__cause__}')
    hostname = gethostname()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT insert_error(%(file_id)s,%(h)s,%(etype)s,%(msg)s,%(from_user)s);',
                        {'h':hostname, 'etype': error.__class__.__name__, 'msg': repr(error), 'file_id': file_id, 'from_user': from_user})

def get_info(file_id):
    """Retrieve information for ``file_id``."""
    with connect() as conn:
        with conn.cursor() as cur:
            query = 'SELECT inbox_path, vault_path, stable_id, header from files WHERE id = %(file_id)s;'
            cur.execute(query, { 'file_id': file_id})
            return cur.fetchone()

def set_status(file_id, status):
    """Updaring File ``file_id`` status."""
    assert file_id, 'Eh? No file_id?'
    LOG.debug(f'Updating status file_id {file_id} with "{status.value}"')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE files SET status = %(status)s WHERE id = %(file_id)s;', {'status': status.value, 'file_id': file_id })

def set_info(file_id, vault_path, vault_filesize, header):
    """Updating information in database for ``file_id``."""
    assert file_id, 'Eh? No file_id?'
    assert vault_path, 'Eh? No vault name?'
    LOG.debug(f'Updating status file_id {file_id}')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE files '
                        'SET status = %(status)s, '
                        '    vault_path = %(vault_path)s, '
                        '    vault_filesize = %(vault_filesize)s, '
                        '    header = %(header)s '
                        'WHERE id = %(file_id)s;',
                        {'status': Status.Archived.value,
                         'file_id': file_id,
                         'vault_path': vault_path,
                         'vault_filesize': vault_filesize,
                         'header': header,
                        })

######################################
##           Async code             ##
######################################

@retry_loop(on_failure=_do_exit)
async def create_pool(loop):
    '''\
    Async function to create a pool of connection to the database.
    Used by the frontend.
    '''
    db_args = fetch_args(CONF)
    return await aiopg.create_pool(**db_args, loop=loop, echo=True)


######################################
##           Decorator              ##
######################################
_channel = None

def catch_error(func):
    '''Decorator to store the raised exception in the database'''
    @wraps(func)
    def wrapper(*args):
        try:
            return func(*args)
        except Exception as e:
            if isinstance(e,AssertionError):
                raise e

            exc_type, _, exc_tb = sys.exc_info()
            g = traceback.walk_tb(exc_tb)
            frame, lineno = next(g) # that should be the decorator
            try:
                frame, lineno = next(g) # that should be where is happened
            except StopIteration:
                pass # In case the trace is too short

            #fname = os.path.split(frame.f_code.co_filename)[1]
            fname = frame.f_code.co_filename
            LOG.error(f'Exception: {exc_type} in {fname} on line: {lineno}')
            from_user = isinstance(e,FromUser)
            cause = e.__cause__ or e
            LOG.error(f'{cause!r} (from user: {from_user})') # repr = Technical

            try:
                data = args[-1] # data is the last argument
                data['status'] = Status.Error.value
                file_id = data.get('file_id', None) # should be there
                if file_id:
                    set_error(file_id, cause, from_user)
                LOG.debug('Catching error on file id: %s', file_id)
                if from_user: # Send to CentralEGA
                    org_msg = data.pop('org_msg', None) # should be there
                    org_msg['status'] = { 'state': 'ERROR', 'message': str(cause) } # str = Informal
                    LOG.info(f'Sending user error to local broker: {org_msg}')
                    global _channel
                    if _channel is None:
                        _channel = get_connection('broker').channel()
                    publish(org_msg, _channel, 'cega', 'files.error')
            except Exception as e2:
                LOG.error(f'While treating "{e}", we caught "{e2!r}"')
                print(repr(e), 'caused', repr(e2), file=sys.stderr)
            return None
    return wrapper

def crypt4gh_to_user_errors(func):
    '''Decorator to convert Crypt4GH exceptions to User Errors'''
    @wraps(func)
    def wrapper(*args):
        try:
            return func(*args)
        except (crypt_exc.InvalidFormatError, crypt_exc.VersionError, crypt_exc.MDCError, PGPKeyError) as e:
            LOG.error(f'Converting {e!r} to a FromUser error')
            raise FromUser() from e
        except KeyserverError as e:
            LOG.critical(repr(e))
            raise
    return wrapper

# Testing connection with `python -m lega.utils.db`
if __name__ == '__main__':
    CONF.setup(sys.argv)
    conn = connect()
    print(conn)
