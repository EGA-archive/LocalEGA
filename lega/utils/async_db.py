# -*- coding: utf-8 -*-

'''
Async Database Connection
'''

import sys
import logging
import traceback
from socket import gethostname

import aiopg

from .db import DBConnection

LOG = logging.getLogger(__name__)

#############################################################
## Async code - Used by data-out
#############################################################

async def create_pool(loop=None):
    db_args = DBConnection('db').fetch_args()
    LOG.info(f"Initializing a connection to: {db_args['user']}@{db_args['host']}:{db_args['port']}/{db_args['database']}")
    return await aiopg.create_pool(**db_args, loop=loop)

async def make_request(pool, stable_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT * FROM local_ega_download.make_request(%(stable_id)s);', {'stable_id': stable_id})
            return await cur.fetchone()

async def download_complete(pool, req_id, dlsize):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT local_ega_download.download_complete(%(req_id)s,%(dlsize)s);',
                              {'req_id': req_id, 'dlsize': dlsize})

async def get(pool, req_id, fields, table='local_ega_download.main'):
    """SELECT *fields FROM table WHERE id = req_id"""
    assert req_id, 'Eh? No req_id?'
    table = table or 'local_ega_download.main'
    LOG.debug(f'Select fields for {req_id} from {table}: {fields}')
    if not fields:
        return None
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            q = ', '.join(fields)
            query = f'SELECT {q} FROM {table} WHERE id = %(req_id)s;' # no sql injection for {table}
            await cur.execute(query, { 'file_id': file_id })
            res = await cur.fetchone()
            if res and len(fields) == 1: # deconstruct if only one field is requested
                res = res[0]
            return res

async def update(pool, req_id, **kwargs):
    """Updating information in database for ``req_id``."""
    if not kwargs:
        return
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            q = ', '.join(f'{k} = %({k})s' for k in kwargs) # keys
            query = f'UPDATE local_ega_download.main SET {q} WHERE id = %(req_id)s;'
            kwargs['req_id'] = req_id
            await cur.execute(query, kwargs)


async def set_error(pool, req_id, error, client_ip=None):

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

    hostname = gethostname()

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT local_ega_download.insert_error(%(req_id)s,%(h)s,%(etype)s,%(msg)s,%(client_ip)s);',
                              {'h':hostname,
                               'etype': error.__class__.__name__,
                               'msg': repr(error),
                               'req_id': req_id,
                               'client_ip': client_ip})
