# -*- coding: utf-8 -*-

"""Database Connection."""

import sys
import logging
import psycopg2
from socket import gethostname
from time import sleep
from contextlib import contextmanager
from functools import wraps
import atexit


from . import redact_url
from ..conf import CONF
from ..conf.logging import _cid
from ..utils import retry

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
        self.args = CONF.getsensitive(self.conf_section, 'connection')
        if isinstance(self.args, bytes):  # secret to str
            self.args = self.args.decode()
        self.interval = CONF.getint(self.conf_section, 'try_interval', fallback=1)
        self.attempts = CONF.getint(self.conf_section, 'try', fallback=1)
        assert self.attempts > 0, "The number of reconnection should be >= 1"


    def connect(self, force=False):
        """Get the database connection (which encapsulates a database session).

        Upon success, the connection is cached.

        Before success, we try to connect ``try`` times every ``try_interval`` seconds (defined in CONF)
        Executes ``on_failure`` after ``try`` attempts.
        """
        if force:
            self.close()

        if self.conn:
            return

        if not self.args:
            self.fetch_args()

        LOG.info("Initializing a connection to %s", redact_url(self.args))

        backoff = self.interval
        for count in range(1,self.attempts+1):
            try:
                self.conn = psycopg2.connect(self.args)
                # self.conn.set_session(autocommit=True) # default is False.
                LOG.debug("Connection successful")
                return
            except psycopg2.OperationalError as e:
                LOG.debug("Database connection error: %r", e)
            except psycopg2.InterfaceError as e:
                LOG.debug("Invalid connection parameters: %r", e)
                break # go to failure
            LOG.debug("Connection attempt %d", count)
            self.conn.close()
            sleep(backoff)
            backoff = (2 ** (count // 10)) * self.interval
            # from  0 to  9, sleep 1 * self.interval secs
            # from 10 to 19, sleep 2 * self.interval secs
            # from 20 to 29, sleep 4 * self.interval secs ... etc
            
        # fail to connect
        if callable(self.on_failure):
            LOG.error("Failed to connect.")
            self.on_failure()

    def ping(self):
        """Ping DB connection."""
        if self.conn is None:
            self.connect()
        try:
            with self.conn: # deal with autocommit
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
        if self.conn:
            self.conn.close()
            self.conn = None

    # Note, the code does not close the database connection nor the cursor
    # if everything goes fine.


######################################
#           Business logic           #
######################################

# Instantiate the global connection
connection = DBConnection(on_failure=lambda: sys.exit(1))

atexit.register(lambda: connection.close())


def insert_job(filename, user_id, encrypted_sha256_checksum=None):
    """Insert a new file entry and returns its id."""
    correlation_id = _cid.get()
    assert correlation_id, 'Eh? No correlation_id?'
    with connection.cursor() as cur:
        cur.execute('''SELECT * FROM ega.insert_job(%(correlation_id)s::text,
                                                    %(filename)s::text,
                                                    %(user_id)s::text,
                                                    %(cs)s::text,
                                                    %(cs_type)s::checksum_algorithm);''',
                    {'correlation_id': _cid.get(),
                     'filename': filename,
                     'user_id': user_id,
                     'cs': encrypted_sha256_checksum,
                     'cs_type': None if encrypted_sha256_checksum is None else 'sha256'})
        _id = (cur.fetchone())[0]
        if _id is None:
            raise Exception('Database issue with insert_job')
        LOG.debug('Inserted job id %s for %s', _id, filename)
        return _id


def set_error(error, from_user=False):
    """Record error to database."""
    correlation_id = _cid.get()
    assert correlation_id, 'Eh? No correlation_id?'
    assert error, 'Eh? No error?'
    LOG.debug('Setting error for %s: %s | Cause: %s', correlation_id, error, error.__cause__)
    with connection.cursor() as cur:
        cur.execute('''SELECT * FROM local_ega.insert_error(%(correlation_id)s,
                                                            %(h)s,
                                                            %(etype)s,
                                                            %(msg)s,
                                                            %(from_user)s);''',
                    {'h': gethostname(),
                     'etype': error.__class__.__name__,
                     'msg': repr(error),
                     'correlation_id': correlation_id,
                     'from_user': from_user})
        return cur.fetchall()


def mark_staged(header, staging_path, staging_checksum, staging_size):

    correlation_id = _cid.get()
    assert correlation_id, 'Eh? No correlation_id?'
    assert header, 'Eh? No header?'
    LOG.debug('Setting status to staged for job %s', correlation_id)
    with connection.cursor() as cur:
        cur.execute('SELECT * FROM local_ega.mark_verified(%(correlation_id)s, '
                    '                                %(h)s, '
                    '                                %(spath)s, '
                    '                                %(ssize)s, '
                    '                                %(sc)s, '
                    '                                %(sct)s)',
                    {'correlation_id': correlation_id,
                     'spath': staging_path,
                     'ssize': staging_size,
                     'sc': staging_checksum,
                     'sct': 'SHA256',
                     'h': header})


def mark_verified(session_key_checksums, digest_sha256):
    """Mark file as verified."""
    correlation_id = _cid.get()
    assert correlation_id, 'Eh? No correlation_id?'
    LOG.debug('Marking correlation_id %s with "VERIFIED"', correlation_id)
    with connection.cursor() as cur:
        cur.execute('UPDATE local_ega.files '
                    'SET status = %(status)s, '
                    '    archive_checksum = %(archive_checksum)s, '
                    '    archive_checksum_type = %(archive_checksum_type)s '
                    'WHERE correlation_id = %(correlation_id)s;',
                    {'status': 'VERIFIED', # no data-race is file status is DISABLED or ERROR
                     'correlation_id': correlation_id, 
                     'archive_checksum': digest_sha256,
                     'archive_checksum_type': 'SHA256'})
        # Insert the checksums, afterwards
        cur.executemany('INSERT INTO local_ega.session_key_checksums_sha256 '
                        '            (correlation_id, session_key_checksum) '
                        'VALUES (%s, %s);',
                        [(correlation_id, c) for c in session_key_checksums])

def set_status(job_id, status):
    """Set job status."""
    assert job_id, 'Eh? No job_id?'
    LOG.debug('Setting job %s to "%s"', job_id, status)
    with connection.cursor() as cur:
        cur.execute('UPDATE local_ega.jobs '
                    'SET status = %(status)s '
                    'WHERE id = %(job_id)s;',
                    {'status': status,
                     'job_id': job_id })
        # Note: no data-race is file status is DISABLED or ERROR

def has_session_keys_checksums(session_key_checksums):
    """Check if this session key is (likely) already used."""
    assert session_key_checksums, 'Eh? No checksum for the session keys?'
    LOG.debug('Check if session keys (hash) are already used: %s', session_key_checksums)
    with connection.cursor() as cur:
        LOG.debug('SELECT * FROM local_ega.has_session_keys_checksums_sha256(%s);', session_key_checksums)
        cur.execute('SELECT * FROM local_ega.has_session_keys_checksums_sha256(%(sk_checksums)s);',
                    {'sk_checksums': list(session_key_checksums)})
        found = cur.fetchone()
        LOG.debug("Check session keys: %s", found)
        return (found and found[0])  # not none and check boolean value

def is_canceled(job_id):
    """Check if this job is marked as not canceled."""
    assert job_id, 'Eh? No job_id?'
    res = False
    with connection.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM local_ega.jobs WHERE id = %(job_id)s AND (status = ANY(%(statuses)s)));",
                    {'job_id': job_id,
                    'statuses': ['CANCELED', 'ERROR', 'COMPLETED'] })   # ie: ongoing job
        found = cur.fetchone()
        res = found and found[0] # not none and check boolean value
    return res

# Testing connection with `python -m crg_ingestion.utils.db`
if __name__ == '__main__':
    with connection.cursor() as cur:
        query = 'SELECT inbox_path, archive_path, stable_id, header from local_ega.files;'
        print('query:', query)
        cur.execute(query)
        names = ('inbox_path', 'archive_path', 'stable_id', 'header')
        for row in cur.fetchall():
            res = [f'{k}: {v}' for k, v in zip(names, row)]
            print('-'*30)
            print(res)
        else:
            print('no rows')
            
