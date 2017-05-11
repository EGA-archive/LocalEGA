# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

'''
####################################
#
# Database Connection
#
####################################
'''

import logging
from enum import Enum
import aiopg
from psycopg2 import connect as db_connect

from .conf import CONF
from .utils import cache_var

LOG = logging.getLogger('db')

class Status(Enum):
    Received = 'Received'
    In_Progress = 'In progress'
    Archived = 'Archived'
    Error = 'Error'
    # Received = 1
    # In_Progress = 2
    # Archived = 3
    # Error = 4

Statements = {
    'insert_submission' : ('INSERT INTO submissions (id, user_id) '
                           'VALUES(%(submission_id)s, %(user_id)s) '
                           'ON CONFLICT (id) DO UPDATE SET created_at = DEFAULT;'),

    'insert_file'       : ('INSERT INTO files (submission_id,filename,filehash,hash_algo,status) '
                           'VALUES(%(submission_id)s,%(filename)s,%(filehash)s,%(hash_algo)s,%(status)s) '
                           'RETURNING files.id;'),

    'update_status'     : 'UPDATE files SET status = %(status)s WHERE id = %(file_id)s;',

    'set_error'         : 'INSERT INTO errors (file_id,msg) VALUES(%(file_id)s,%(msg)s) RETURNING errors.id;',

    'get_info'          : 'SELECT filename, status, created_at, last_modified FROM files WHERE id = %(file_id)s',

    'set_encryption'    : 'UPDATE files SET reenc_info = %(reenc_info)s, reenc_key = %(reenc_key)s WHERE id = %(file_id)s;',

    'set_stable_id'     : 'UPDATE files SET stable_id = %(stable_id)s WHERE id = %(file_id)s;',

}

######################################
##           Async code             ##
######################################
async def create_pool(loop, **kwargs):
    return await aiopg.create_pool(**kwargs,loop=loop, echo=True)

async def insert_submission(pool, **kwargs):
    LOG.debug(kwargs)
    with (await pool.cursor()) as cur:
        query = Statements['insert_submission']
        await cur.execute(query, kwargs)

async def insert_file(pool, **kwargs):
    if not kwargs.pop('status', None):
        kwargs['status'] = Status.Received.value
    LOG.debug(kwargs)
    with (await pool.cursor()) as cur:
        query = Statements['insert_file']
        await cur.execute(query, kwargs)
        return (await cur.fetchone())[0] # returning the id

async def aio_get_info(pool, file_id):
    assert file_id, 'Eh? No file_id?'
    with (await pool.cursor()) as cur:
        query = Statements['get_info']
        await cur.execute(query, {'file_id': file_id})
        return await cur.fetchone()

# async def aio_update_status(pool, file_id, status):
#     with (await pool.cursor()) as cur:
#         query = Statements['update_status']
#         await cur.execute(query, {'status': status.value, 'file_id': file_id})
    
async def aio_set_error(pool, file_id, error):
    assert file_id, 'Eh? No file_id?'
    assert error, 'Eh? No error?'
    LOG.debug(f'Async Setting error for {file_id}: {error}')
    with (await pool.cursor()) as cur:
        query = Statements['set_error']
        await cur.execute(query, {'msg':error, 'file_id': file_id})

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
    return db_connect(user=user, password=password, database=database, host=host, port=port)

def update_status(file_id, status):
    assert file_id, 'Eh? No file_id?'
    assert status, 'Eh? No status?'
    LOG.debug(f'Updating status file_id {file_id}: {status!r}')
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['update_status']
            cur.execute(query, {'status': status.value, 'file_id': file_id})
            #
            # Marking submission as completed is done as a DB trigger
            # We save a few round trips with queries and connections
            
    
def set_error(file_id, error):
    assert file_id, 'Eh? No file_id?'
    assert error, 'Eh? No error?'
    LOG.debug(f'Setting error for {file_id}: {error}')
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['set_error']
            cur.execute(query, {'msg':error, 'file_id': file_id})

def set_encryption(file_id, info, key):
    assert file_id, 'Eh? No file_id?'
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['set_encryption']
            cur.execute(query, {'reenc_info': info, 'reenc_key': key, 'file_id': file_id})

def set_stable_id(file_id, stable_id):
    assert file_id, 'Eh? No file_id?'
    assert stable_id, 'Eh? No stable_id?'
    LOG.debug(f'Setting final name for file_id {file_id}: {stable_id}')
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['set_stable_id']
            cur.execute(query, {'stable_id': stable_id, 'file_id': file_id})
