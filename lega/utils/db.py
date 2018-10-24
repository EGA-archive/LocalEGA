# -*- coding: utf-8 -*-

"""Database Connection."""

import sys
import traceback
from functools import wraps
import logging
import psycopg2
from socket import gethostname
from contextlib import contextmanager
from time import sleep

from legacryptor import exceptions as crypt_exc

from .exceptions import FromUser, KeyserverError, PGPKeyError

LOG = logging.getLogger(__name__)


######################################
#          DB connection             #
######################################
class DBConnection():
    conn = None
    curr = None
    args = None

    def __init__(self, user, password, database, host, port, nb_try=1, connect_timeout=1, on_failure=None):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.connect_timeout=connect_timeout
        self.on_failure = on_failure

        assert nb_try > 0, "The number of reconnection should be >= 1"
        self.nb_try = nb_try

    @property
    def fetch_args(self):
        return { 'user': self.user,
                 'password': self.password,
                 'database': self.database,
                 'host': self.host,
                 'port': self.port,
                 'connect_timeout': self.connect_timeout
                 #'sslmode': self.conf.get_value(self.conf_section, 'sslmode'),
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

        args = self.fetch_args
        LOG.info(f"Initializing a connection to: {args['host']}:{args['port']}/{args['database']}")

        LOG.debug(f"{self.nb_try} attempts")
        count = 0
        while count < self.nb_try:
            try:
                LOG.debug(f"Connection attempt {count+1}")
                self.conn = psycopg2.connect(**self.fetch_args)
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


class DB(object):
    connection = None

    def __init__(self, user, password, database, host, port, nb_try=1, connect_timeout=1, on_failure=None):
        self.connection = DBConnection(user, password, database, host, port, nb_try, connect_timeout, on_failure)


    def insert_file(self, filename, user_id):
        """Insert a new file entry and returns its id"""
        with self.connection.cursor() as cur:
            cur.execute('SELECT insert_file(%(filename)s,%(user_id)s);',
                        { 'filename': filename,
                          'user_id': user_id,
                        })
            file_id = (cur.fetchone())[0]
            if file_id:
                LOG.debug(f'Created id {file_id} for {filename}')
                return file_id
            else:
                raise Exception('Database issue with insert_file')

    def set_error(self, file_id, error, from_user=False):
        """Store error related to ``file_id`` in database."""
        assert file_id, 'Eh? No file_id?'
        assert error, 'Eh? No error?'
        LOG.debug(f'Setting error for {file_id}: {error!s} | Cause: {error.__cause__}')
        hostname = gethostname()
        with self.connection.cursor() as cur:
            cur.execute('SELECT insert_error(%(file_id)s,%(h)s,%(etype)s,%(msg)s,%(from_user)s);',
                        {'h':hostname, 'etype': error.__class__.__name__, 'msg': repr(error), 'file_id': file_id, 'from_user': from_user})



    def get_info(self, file_id):
        """Retrieve information for ``file_id``."""
        with self.connection.cursor() as cur:
            query = 'SELECT inbox_path, vault_path, stable_id, header from files WHERE id = %(file_id)s;'
            cur.execute(query, {'file_id': file_id})
            return cur.fetchone()


    def _set_status(self,file_id, status):
        """Update status for file with id ``file_id``."""
        assert file_id, 'Eh? No file_id?'
        LOG.debug(f'Updating status file_id {file_id} with "{status}"')
        with self.connection.cursor() as cur:
            cur.execute('UPDATE files SET status = %(status)s WHERE id = %(file_id)s;',
                        {'status': status,
                         'file_id': file_id})


    def mark_in_progress(file_id):
        """Mark file in progress."""
        return self._set_status(file_id, 'In progress')

    def mark_completed(file_id):
        """Mark file as completed."""
        return self._set_status(file_id, 'Completed')

    def set_stable_id(self, file_id, stable_id):
        """Update File ``file_id`` stable ID."""
        assert file_id, 'Eh? No file_id?'
        LOG.debug(f'Updating file_id {file_id} with stable ID "{stable_id}"')
        with self.connection.cursor() as cur:
            cur.execute('UPDATE files '
                        'SET status = %(status)s, '
                        '    stable_id = %(stable_id)s '
                        'WHERE id = %(file_id)s;',
                        {'status': 'Ready',
                         'file_id': file_id,
                         'stable_id': stable_id})

    def store_header(self, file_id, header):
        """Store header for ``file_id``."""
        assert file_id, 'Eh? No file_id?'
        assert header, 'Eh? No header?'
        LOG.debug(f'Store header for file_id {file_id}')
        with self.connection.cursor() as cur:
            cur.execute('UPDATE files '
                        'SET header = %(header)s '
                        'WHERE id = %(file_id)s;',
                        {'file_id': file_id,
                         'header': header})

    def set_archived(self, file_id, vault_path, vault_filesize):
        """Archive ``file_id``."""
        assert file_id, 'Eh? No file_id?'
        assert vault_path, 'Eh? No vault name?'
        LOG.debug(f'Setting status to archived for file_id {file_id}')
        with self.connection.cursor() as cur:
            cur.execute('UPDATE files '
                        'SET status = %(status)s, '
                        '    vault_path = %(vault_path)s, '
                        '    vault_filesize = %(vault_filesize)s '
                        'WHERE id = %(file_id)s;',
                        {'status': 'Archived',
                         'file_id': file_id,
                         'vault_path': vault_path,
                         'vault_filesize': vault_filesize})


######################################
#            Decorator               #
######################################


def crypt4gh_to_user_errors(func):
    """Convert Crypt4GH exceptions to User Errors decorator."""
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
#if __name__ == '__main__':
#    CONF.setup(sys.argv)
#    conn = connect()
#    print(conn)
