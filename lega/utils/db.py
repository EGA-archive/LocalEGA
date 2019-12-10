# -*- coding: utf-8 -*-

"""Database Connection."""

import sys
import logging
import traceback
from functools import wraps
import psycopg2
from socket import gethostname
from time import sleep
from contextlib import contextmanager


from ..conf import CONF
from .exceptions import FromUser
from .amqp import publish, get_connection

LOG = logging.getLogger(__name__)


######################################
#          DB connection             #
######################################

class DBConnection():
    """Databse connection setup."""

    conn = None
    curr = None
    args = None
    interval = None
    attempts = None

    def __init__(self, conf_section='db', on_failure=None):
        """Initialize config section parameters for DB and failure fallback."""
        self.on_failure = on_failure
        self.conf_section = conf_section or 'db'

    def fetch_args(self):
        """Fetch arguments for initializing a connection to db."""
        self.args = CONF.get_value(self.conf_section, 'connection')
        self.interval = CONF.get_value(self.conf_section, 'try_interval', conv=int, default=1)
        self.attempts = CONF.get_value(self.conf_section, 'try', conv=int, default=1)
        assert self.attempts > 0, "The number of reconnection should be >= 1"

    def connect(self, force=False):
        """Get the database connection (which encapsulates a database session).

        Upon success, the connection is cached.

        Before success, we try to connect ``try`` times every ``try_interval`` seconds (defined in CONF)
        Executes ``on_failure`` after ``try`` attempts.
        """
        if force:
            self.close()

        if self.conn and self.curr:
            return

        if not self.args:
            self.fetch_args()
        LOG.info("Initializing a connection")

        LOG.debug("%s attempts", self.attempts)
        backoff = self.interval
        for count in range(self.attempts):
            try:
                LOG.debug("Connection attempt %d: %s", count, self.args)
                self.conn = psycopg2.connect(self.args)
                # self.conn.set_session(autocommit=True) # default is False.
                LOG.debug("Connection successful")
                return
            except psycopg2.OperationalError as e:
                LOG.debug("Database connection error: %r", e)
            except psycopg2.InterfaceError as e:
                LOG.debug("Invalid connection parameters: %r", e)
                break
            sleep(backoff)
            backoff = (2 ** (count // 10)) * self.interval
            # from  0 to  9, sleep 1 * self.interval secs
            # from 10 to 19, sleep 2 * self.interval secs
            # from 20 to 29, sleep 4 * self.interval secs ... etc

        # fail to connect
        if self.on_failure:
            self.on_failure()

    def ping(self):
        """Ping DB connection."""
        if self.conn is None:
            self.connect()
        try:
            with self.conn:
                with self.conn.cursor() as cur:  # does not commit if error raised
                    cur.execute('SELECT 1;')
                    LOG.debug("Ping db successful")
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            LOG.debug('Ping failed: %s', e)
            self.connect(force=True)  # reconnect

    @contextmanager
    def cursor(self):
        """Return DB Cursor, thus reusing it."""
        self.ping()
        with self.conn:
            with self.conn.cursor() as cur:
                yield cur
                # closes cursor on exit
            # transaction autocommit, but connection not closed

    def close(self):
        """Close DB Connection."""
        LOG.debug("Closing the database")
        if self.curr:
            self.curr.close()
            self.curr = None
        if self.conn:
            self.conn.close()
            self.conn = None

# Note, the code does not close the database connection nor the cursor
# if everything goes fine.

def _do_exit():
    """Exit on error."""
    LOG.error("Could not connect to the database: Exiting")
    sys.exit(1)


connection = DBConnection()

######################################
#           Business logic           #
######################################

def insert_file(filename, user_id):
    """Insert a new file entry and returns its id."""
    with connection.cursor() as cur:
        cur.execute('SELECT local_ega.insert_file(%(filename)s,%(user_id)s);',
                    {'filename': filename,
                     'user_id': user_id,
                    })
        file_id = (cur.fetchone())[0]
        if file_id:
            LOG.debug('Created id %s for %s', file_id, filename)
            return file_id
        raise Exception('Database issue with insert_file')

def set_error(file_id, error, from_user=False):
    """Store error related to ``file_id`` in database."""
    assert file_id, 'Eh? No file_id?'
    assert error, 'Eh? No error?'
    LOG.debug('Setting error for %s: %s | Cause: %s', file_id, error, error.__cause__)
    hostname = gethostname()
    with connection.cursor() as cur:
        cur.execute('SELECT * FROM local_ega.insert_error(%(file_id)s,%(h)s,%(etype)s,%(msg)s,%(from_user)s);',
                    {'h': hostname,
                     'etype': error.__class__.__name__,
                     'msg': repr(error),
                     'file_id': file_id,
                     'from_user': from_user})
        return cur.fetchall()


def get_info(file_id):
    """Retrieve information for ``file_id``."""
    with connection.cursor() as cur:
        query = 'SELECT inbox_path, archive_path, stable_id, header from local_ega.files WHERE id = %(file_id)s;'
        cur.execute(query, {'file_id': file_id})
        return cur.fetchone()


def _set_status(file_id, status):
    """Update status for file with id ``file_id``."""
    assert file_id, 'Eh? No file_id?'
    with connection.cursor() as cur:
        cur.execute('UPDATE local_ega.files SET status = %(status)s WHERE id = %(file_id)s;',
                    {'status': status,
                     'file_id': file_id})


def mark_in_progress(file_id):
    """Mark file in progress."""
    LOG.debug('Marking file_id %s with "IN_INGESTION"', file_id)
    return _set_status(file_id, 'IN_INGESTION')


def mark_completed(file_id):
    """Mark file as completed."""
    LOG.debug('Marking file_id %s with "COMPLETED"', file_id)
    return _set_status(file_id, 'COMPLETED')


def set_stable_id(file_id, stable_id):
    """Update File ``file_id`` stable ID."""
    assert file_id, 'Eh? No file_id?'
    LOG.debug('Updating file_id %s with stable ID "%s"', file_id, stable_id)
    with connection.cursor() as cur:
        cur.execute('UPDATE local_ega.files '
                    'SET status = %(status)s, '
                    '    stable_id = %(stable_id)s '
                    'WHERE id = %(file_id)s;',
                    {'status': 'READY',
                     'file_id': file_id,
                     'stable_id': stable_id})


def store_header(file_id, header):
    """Store header for ``file_id``."""
    assert file_id, 'Eh? No file_id?'
    assert header, 'Eh? No header?'
    LOG.debug('Store header for file_id %s', file_id)
    with connection.cursor() as cur:
        cur.execute('UPDATE local_ega.files '
                    'SET header = %(header)s '
                    'WHERE id = %(file_id)s;',
                    {'file_id': file_id,
                     'header': header})


def set_archived(file_id, archive_path, archive_filesize):
    """Archive ``file_id``."""
    assert file_id, 'Eh? No file_id?'
    assert archive_path, 'Eh? No archive name?'
    LOG.debug('Setting status to archived for file_id %s', file_id)
    with connection.cursor() as cur:
        cur.execute('UPDATE local_ega.files '
                    'SET status = %(status)s, '
                    '    archive_path = %(archive_path)s, '
                    '    archive_filesize = %(archive_filesize)s '
                    'WHERE id = %(file_id)s;',
                    {'status': 'ARCHIVED',
                     'file_id': file_id,
                     'archive_path': archive_path,
                     'archive_filesize': archive_filesize})


######################################
#            Decorator               #
######################################
_channel = None


def catch_error(func):  # noqa: C901
    """Store the raised exception in the database decorator."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, AssertionError):
                raise e

            exc_type, _, exc_tb = sys.exc_info()
            g = traceback.walk_tb(exc_tb)
            frame, lineno = next(g)  # that should be the decorator
            try:
                frame, lineno = next(g)  # that should be where is happened
            except StopIteration:
                pass  # In case the trace is too short

            fname = frame.f_code.co_filename
            LOG.error('Exception: %s in %s on line: %s', exc_type, fname, lineno)
            from_user = isinstance(e, FromUser)
            cause = e.__cause__ or e
            LOG.error('%r (from user: %s)', cause, from_user)  # repr = Technical

            try:
                data = args[-1]  # data is the last argument
                file_id = data.get('file_id', None)  # should be there
                if file_id:
                    set_error(file_id, cause, from_user)
                LOG.debug('Catching error on file id: %s', file_id)
                if from_user:  # Send to CentralEGA
                    org_msg = data.pop('org_msg', None)  # should be there
                    org_msg['reason'] = str(cause)  # str = Informal
                    LOG.info('Sending user error to local broker: %s', org_msg)
                    global _channel
                    if _channel is None:
                        _channel = get_connection('broker').channel()
                    publish(org_msg, _channel, 'cega', 'files.error')
            except Exception as e2:
                LOG.error('While treating "%s", we caught "%r"', e, e2)
                print(repr(e), 'caused', repr(e2), file=sys.stderr)
            return None
    return wrapper


def crypt4gh_to_user_errors(func):
    """Convert Crypt4GH exceptions to User Errors decorator."""
    @wraps(func)
    def wrapper(*args):
        try:
            return func(*args)
        except ValueError as e:
            LOG.error('Converting %r to a FromUser error', e)
            raise FromUser() from e
    return wrapper


# Testing connection with `python -m lega.utils.db`
if __name__ == '__main__':
    CONF.setup()
    with connection.cursor() as cur:
        query = 'SELECT inbox_path, archive_path, stable_id, header from local_ega.files;'
        cur.execute(query)
        names = ('inbox_path', 'archive_path', 'stable_id', 'header')
        for row in cur.fetchall():
            res = [f'{k}: {v}' for k,v in zip(names, row)]
            print('-'*30)
            print(res)
