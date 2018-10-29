# -*- coding: utf-8 -*-

'''
Database Connection
'''

import sys
import traceback
import logging
import psycopg2
from socket import gethostname
import inspect
from contextlib import contextmanager

from ..conf import CONF

LOG = logging.getLogger(__name__)

######################################
##         DB connection            ##
######################################
def _do_exit():
    LOG.error("Could not connect to the database: Exiting")
    sys.exit(1)

class DBConnection():
    conn = None
    curr = None
    args = None

    def __init__(self, conf_section='db', on_failure=None):
        self.on_failure = on_failure
        self.conf_section = conf_section or 'db'

    def fetch_args(self):
        return { 'user': CONF.get_value(self.conf_section, 'user'),
                 'password': CONF.get_value(self.conf_section, 'password'),
                 'database': CONF.get_value(self.conf_section, 'database'),
                 'host': CONF.get_value(self.conf_section, 'host'),
                 'port': CONF.get_value(self.conf_section, 'port', conv=int),
                 'connect_timeout': CONF.get_value(self.conf_section, 'try_interval', conv=int, default=1),
                 'sslmode': CONF.get_value(self.conf_section, 'sslmode'),
        }


    def connect(self, force=False):
        '''Get the database connection (which encapsulates a database session)

        Upon success, the connection is cached.

        Before success, we try to connect ``try`` times every ``try_interval`` seconds (defined in CONF)
        Executes ``on_failure`` after ``try`` attempts.
        '''

        if force:
            self.close()

        if self.conn and self.curr:
            return

        if not self.args:
            self.args = self.fetch_args()
        LOG.info(f"Initializing a connection to: {self.args['host']}:{self.args['port']}/{self.args['database']}")

        nb_try = CONF.get_value('postgres', 'try', conv=int, default=1)
        assert nb_try > 0, "The number of reconnection should be >= 1"
        LOG.debug(f"{nb_try} attempts")
        count = 0
        while count < nb_try:
            try:
                LOG.debug(f"Connection attempt {count+1}")
                self.conn = psycopg2.connect(**self.args)
                #self.conn.set_session(autocommit=True) # default is False.
                LOG.debug(f"Connection successful")
                return
            except psycopg2.OperationalError as e:
                LOG.debug(f"Database connection error: {e!r}")
                count += 1
            except psycopg2.InterfaceError as e:
                LOG.debug(f"Invalid connection parameters: {e!r}")
                break

        # fail to connect
        if self.on_failure:
            self.on_failure()

    def ping(self):
        if self.conn is None:
            self.connect()
        try:
            with self.conn:
                with self.conn.cursor() as cur: # does not commit if error raised
                    cur.execute('SELECT 1;')
                    LOG.debug("Ping db successful")
        except psycopg2.OperationalError as e:
            LOG.debug('Ping failed: %s', e)
            self.connect(force=True) # reconnect

    @contextmanager
    def cursor(self):
        self.ping()
        with self.conn:
            with self.conn.cursor() as cur:
                yield cur
                # closes cursor on exit
            # transaction autocommit, but connection not closed

    def close(self):
        LOG.debug("Closing the database")
        if self.curr:
            self.curr.close()
            self.curr = None
        if self.conn:
            self.conn.close()
            self.conn = None

# Note, the code does not close the database connection nor the cursor
# if everything goes fine.

######################################
##         Business logic           ##
######################################
connection = DBConnection()

def insert_file(filename, user_id):
    """Insert a new file entry and returns its id"""
    with connection.cursor() as cur:
        cur.execute('SELECT local_ega.insert_file(%(filename)s,%(user_id)s);',
                    { 'filename': filename,
                      'user_id': user_id,
                    })
        file_id = (cur.fetchone())[0]
        if file_id:
            LOG.debug(f'Created id {file_id} for {filename}')
            return file_id
        else:
            raise Exception('Database issue with insert_file')

def set_error(file_id, error, from_user=False):
    """Store error related to ``file_id`` in database."""
    assert file_id, 'Eh? No file_id?'
    assert error, 'Eh? No error?'
    LOG.debug(f'Setting error for {file_id}: {error!s} | Cause: {error.__cause__}')
    hostname = gethostname()
    with connection.cursor() as cur:
        cur.execute('SELECT local_ega.insert_error(%(file_id)s,%(h)s,%(etype)s,%(msg)s,%(from_user)s);',
                    {'h':hostname, 'etype': error.__class__.__name__, 'msg': repr(error), 'file_id': file_id, 'from_user': from_user})

def update(file_id, kwargs):
    """Updating information in database for ``file_id``."""
    assert file_id, 'Eh? No file_id?'
    LOG.debug(f'Updating status file_id {file_id} with {kwargs}')
    if not kwargs:
        return
    with connection.cursor() as cur:
        q = ', '.join(f'{k} = %({k})s' for k in kwargs) # keys
        query = f'UPDATE local_ega.files SET {q} WHERE id = %(file_id)s;'
        kwargs['file_id'] = file_id
        cur.execute(query, kwargs)

def finalize(kwargs):
    """Flag as done and insert stable_id."""
    LOG.debug('Finalizing %s', kwargs)
    for k in ('filepath', 'user', 'checksum', 'checksum_type', 'stable_id'):
        if k not in kwargs:
            raise ValueError(f'Missing key: {k} in {kwargs}')
    with connection.cursor() as cur:
        cur.execute('SELECT local_ega.finalize_file(%(filepath)s,'
                    '                               %(user)s,'
                    '                               %(checksum)s,'
                    '                               %(checksum_type)s,'
                    '                               %(stable_id)s'
                    ');', kwargs)

def is_disabled(file_id):
    """Should we continue handle this file_id?"""
    assert file_id, 'Eh? No file_id?'
    LOG.debug('Is disabled %d?', file_id)
    with connection.cursor() as cur:
        cur.execute('SELECT * FROM local_ega.is_disabled(%(file_id)s);', { 'file_id': file_id })
        return (cur.fetchone())[0]
    
# Raise exception for the moment.
def check_session_key_checksum(session_key_checksum, session_key_checksum_type):
    """Check if this session key is (likely) already used."""
    assert session_key_checksum, 'Eh? No session_key_checksum?'
    LOG.debug(f'Check if session key (hash) "{session_key_checksum}" is already used')
    with connection.cursor() as cur:
        cur.execute('SELECT * FROM local_ega.check_session_key_checksum(%(sk_checksum)s,'
                    '                                                   %(sk_checksum_type)s);',
                    {'sk_checksum': session_key_checksum,
                     'sk_checksum_type': session_key_checksum_type})
        found = cur.fetchone()
        LOG.debug("Check session key: %s", found)
        return (found and found[0]) # not none and check boolean value

# Testing connection with `python -m lega.utils.db`
if __name__ == '__main__':
    CONF.setup(sys.argv)
    with connection.cursor() as cur:
        print(cur)
    connection.close()


