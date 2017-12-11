# -*- coding: utf-8 -*-

'''
####################################
#
# Database Connection
#
####################################
'''

import sys
import traceback
from functools import wraps
import logging
from enum import Enum
import aiopg
import psycopg2
import traceback
from socket import gethostname
from time import sleep
import asyncio

from ..conf import CONF
from .exceptions import FromUser

LOG = logging.getLogger('db')

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
    db_args = { 'user'     : d.get('db','username'),
                'password' : d.get('db','password'),
                'database' : d.get('db','dbname'),
                'host'     : d.get('db','host'),
                'port'     : d.getint('db','port')
    }
    LOG.info(f"Initializing a connection to: {db_args['host']}:{db_args['port']}/{db_args['database']}")
    return db_args

async def _retry(run, on_failure=None, exception=psycopg2.OperationalError):
    '''Main retry loop'''
    nb_try   = CONF.getint('db','try', fallback=1)
    try_interval = CONF.getint('db','try_interval', fallback=1)
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
    '''\
    Decorator retry something `try` times every `try_interval` seconds.
    Run the `on_failure` if after `try` attempts (configured in CONF).
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

async def get_file_info(conn, filename, username):
    assert filename, 'Eh? No filename?'
    assert username, 'Eh? No username?'
    try:
        with (await conn.cursor()) as cur:
            query = 'SELECT file_info(%(filename)s, %(username)s);'
            await cur.execute(query, {'filename': filename, 'username':username})
            return await cur.fetchone()
    except psycopg2.InternalError as pgerr:
        LOG.debug(f'File Info for {filename} (User: {username}): {pgerr!r}')
        return None


async def get_user_info(conn, username):
    assert username, 'Eh? No username?'
    with (await conn.cursor()) as cur:
        query = 'SELECT userfiles_info(%(username)s);'
        await cur.execute(query, {'username': username})
        return await cur.fetchone()

async def flush_user(conn, name):
    with (await conn.cursor()) as cur:
        await cur.execute('SELECT flush_user(%(name)s);', { 'name': name })
        return await cur.fetchone()

######################################
##         "Classic" code           ##
######################################
def cache_connection(func):
    '''Decorator to cache the database connection'''
    cache = {} # must be a dict or an array
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'conn' not in cache or cache['conn'].closed:
            cache['conn'] = func(*args, **kwargs)
        return cache['conn']
    return wrapper

@cache_connection
@retry_loop(on_failure=_do_exit)
def connect():
    '''Get the database connection (which encapsulates a database session)

    Upon success, the connection is cached.

    Before success, we try to connect `try` times every `try_interval` seconds (defined in CONF)
    '''
    db_args = fetch_args(CONF)
    return psycopg2.connect(**db_args)


def insert_file(filename, user_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT insert_file(%(filename)s,%(user_id)s,%(status)s);',{
                'filename': filename,
                'user_id': user_id,
                'status' : Status.Received.value })
            file_id = (cur.fetchone())[0]
            if file_id:
                LOG.debug(f'Created id {file_id} for {filename}')
                return file_id
            else:
                raise Exception('Database issue with insert_file')
 

def get_errors(from_user=False):
    query = 'SELECT * from errors WHERE from_user = true;' if from_user else 'SELECT * from errors;'
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

def set_error(file_id, error):
    assert file_id, 'Eh? No file_id?'
    assert error, 'Eh? No error?'
    LOG.debug(f'Setting error for {file_id}: {error!s}')
    from_user = isinstance(error,FromUser)
    hostname = gethostname()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT insert_error(%(file_id)s,%(msg)s,%(from_user)s);',
                        {'msg':f"[{hostname}][{error.__class__.__name__}] {error!s}", 'file_id': file_id, 'from_user': from_user})

def get_details(file_id):
    with connect() as conn:
        with conn.cursor() as cur:
            query = 'SELECT filename, org_checksum, org_checksum_algo, stable_id, reenc_checksum from files WHERE id = %(file_id)s;'
            cur.execute(query, { 'file_id': file_id})
            return cur.fetchone()

def set_progress(file_id, staging_name, enc_checksum, enc_checksum_algo, org_checksum, org_checksum_algo):
    assert file_id, 'Eh? No file_id?'
    assert staging_name, 'Eh? No staging name?'
    LOG.debug(f'Updating status file_id {file_id}')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE files '
                        'SET status = %(status)s, '
                        '    staging_name = %(name)s, '
                        '    enc_checksum = %(enc_checksum)s, enc_checksum_algo = %(enc_checksum_algo)s, '
                        '    org_checksum = %(org_checksum)s, org_checksum_algo = %(org_checksum_algo)s '
                        'WHERE id = %(file_id)s;',
                        {'status': Status.In_Progress.value,
                         'file_id': file_id,
                         'name': staging_name,
                         'enc_checksum': enc_checksum, 'enc_checksum_algo': enc_checksum_algo,
                         'org_checksum': org_checksum, 'org_checksum_algo': org_checksum_algo,
                        })

def set_encryption(file_id, info, digest):
    assert file_id, 'Eh? No file_id?'
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE files SET reenc_info = %(reenc_info)s, reenc_checksum = %(digest)s, status = %(status)s WHERE id = %(file_id)s;',
                        {'reenc_info': info, 'file_id': file_id, 'digest': digest, 'status': Status.Completed.value})

def finalize_file(file_id, stable_id, filesize):
    assert file_id, 'Eh? No file_id?'
    assert stable_id, 'Eh? No stable_id?'
    LOG.debug(f'Setting final name for file_id {file_id}: {stable_id}')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE files '
                        'SET status = %(status)s, stable_id = %(stable_id)s, reenc_size = %(filesize)s '
                        'WHERE id = %(file_id)s;',
                        {'stable_id': stable_id, 'file_id': file_id, 'status': Status.Archived.value, 'filesize': filesize})

######################################
##           Decorator              ##
######################################

def catch_error(func):
    '''Decorator to store the raised exception in the database'''
    @wraps(func)
    def wrapper(*args):
        try:
            res = func(*args)
            return res
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
            LOG.debug(f'Exception: {exc_type} in {fname} on line: {lineno}')

            try:
                data = args[-1]
                file_id = data['file_id'] # I should have it
                set_error(file_id, e)
            except Exception as e2:
                LOG.error(f'Exception: {e!r}')
                print(repr(e), file=sys.stderr)
            return None
    return wrapper

# Testing connection with `python -m lega.utils.db`
if __name__ == '__main__':
    CONF.setup(sys.argv)
    conn = connect()
    print(conn)
