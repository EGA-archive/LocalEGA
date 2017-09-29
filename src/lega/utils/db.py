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
from functools import wraps
from socket import gethostname

from ..conf import CONF
from .exceptions import FromUser

LOG = logging.getLogger('db')

class Status(Enum):
    Received = 'Received'
    In_Progress = 'In progress'
    Completed = 'Completed'
    Archived = 'Archived'
    Error = 'Error'

def cache_var(v):
    '''Decorator to cache into a global variable'''
    def decorator(func):
        def wrapper(*args, **kwargs):
            g = globals()
            if v not in g:
                g[v] = func(*args, **kwargs)
            return g[v]
        return wrapper
    return decorator

######################################
##           Async code             ##
######################################
async def create_pool(loop, **kwargs):
    return await aiopg.create_pool(**kwargs,loop=loop, echo=True)

async def get_file_info(pool, file_id):
    assert file_id, 'Eh? No file_id?'
    with (await pool.cursor()) as cur:
        query = 'SELECT filename, status, created_at, last_modified, stable_id FROM files WHERE id = %(file_id)s'
        await cur.execute(query, {'file_id': file_id})
        return await cur.fetchone()

async def get_user_info(pool, user_id):
    assert user_id, 'Eh? No user_id?'
    with (await pool.cursor()) as cur:
        query = 'SELECT filename, status, created_at, last_modified, stable_id FROM files WHERE user_id = %(user_id)s'
        await cur.execute(query, {'user_id': user_id})
        return await cur.fetchall()

######################################
##         "Classic" code           ##
######################################

@cache_var('DB_CONNECTION')
def connect():
    '''Get the database connection (which encapsulates a database session)'''
    user     = CONF.get('db','username')
    password = CONF.get('db','password')
    database = CONF.get('db','dbname')
    host     = CONF.get('db','host')
    port     = CONF.getint('db','port')
    LOG.info(f"Initializing a connection to: {host}:{port}/{database}")
    return psycopg2.connect(user=user, password=password, database=database, host=host, port=port)

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


def insert_user(user_id, password_hash, pubkey):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT insert_user(%(uid)s,%(ph)s,%(pk)s);',
                        { 'uid': user_id,
                          'ph': password_hash,
                          'pk': pubkey })
            internal_id = (cur.fetchone())[0]
            if internal_id:
                LOG.debug(f'User {user_id} added to the database (as entry {internal_id}).')
            else:
                raise Exception('Database issue with insert_user')

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

            exc_type, exc_obj, exc_tb = sys.exc_info()
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
