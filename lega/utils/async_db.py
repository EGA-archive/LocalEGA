# -*- coding: utf-8 -*-

'''
Async Database Connection
'''

import sys
import logging
import traceback
from socket import gethostname
#from contextlib import asynccontextmanager
from async_generator import asynccontextmanager

import psycopg2
import aiopg

from ..conf import CONF

LOG = logging.getLogger(__name__)

class DBConnection():
    pool = None
    args = None

    def __init__(self, conf_section='db', on_failure=None, loop=None):
        self.on_failure = on_failure
        self.conf_section = conf_section or 'db'
        self.loop = loop

    def fetch_args(self):
        return { 'user': CONF.get_value(self.conf_section, 'user'),
                 'password': CONF.get_value(self.conf_section, 'password'),
                 'database': CONF.get_value(self.conf_section, 'database'),
                 'host': CONF.get_value(self.conf_section, 'host'),
                 'port': CONF.get_value(self.conf_section, 'port', conv=int),
                 'connect_timeout': CONF.get_value(self.conf_section, 'try_interval', conv=int, default=1),
                 'sslmode': CONF.get_value(self.conf_section, 'sslmode'),
        }


    async def connect(self, force=False):
        '''Get the database connection (which encapsulates a database session)

        Upon success, the connection is cached.

        Before success, we try to connect ``try`` times every ``try_interval`` seconds (defined in CONF)
        Executes ``on_failure`` after ``try`` attempts.
        '''

        if force:
            self.close()

        if self.pool:
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
                self.pool = await aiopg.create_pool(**self.args, loop=self.loop)
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

    async def ping(self):
        if self.pool is None:
            await self.connect()
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    cur.execute('SELECT 1;')
                    LOG.debug("Ping db successful")
        except psycopg2.OperationalError as e:
            LOG.debug('Ping failed: %s', e)
            self.connect(force=True) # reconnect

    @asynccontextmanager
    async def cursor(self):
        await self.ping()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                yield cur
                # closes cursor on exit
            # transaction autocommit, but connection not closed

    async def close(self):
        LOG.debug("Closing the database")
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

#############################################################
## Async code - Used by data-out
#############################################################
connection = DBConnection()

async def make_request(stable_id, user_info, client_ip, start_coordinate=0, end_coordinate=None):
    async with connection.cursor() as cur:
        await cur.execute('SELECT * FROM local_ega_download.make_request(%(stable_id)s,%(user_info)s,%(client_ip)s,%(start_coordinate)s,%(end_coordinate)s);', {'stable_id': stable_id,
                'user_info': user_info,
                'client_ip': client_ip,
                'start_coordinate': start_coordinate,
                'end_coordinate': end_coordinate})
        return await cur.fetchone()

async def download_complete(req_id, dlsize):
    async with connection.cursor() as cur:
        await cur.execute('SELECT local_ega_download.download_complete(%(req_id)s,%(dlsize)s);',
                          {'req_id': req_id, 'dlsize': dlsize})

async def set_error(req_id, error):

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

    async with connection.cursor() as cur:
        await cur.execute('SELECT local_ega_download.insert_error(%(req_id)s,%(h)s,%(etype)s,%(msg)s);',
                          {'h':hostname,
                           'etype': error.__class__.__name__,
                           'msg': repr(error),
                           'req_id': req_id})

async def update_status(req_id, status):
    async with connection.cursor() as cur:
        await cur.execute('SELECT local_ega_download.update_status(%(req_id)s,%(status)s);',
                          {'req_id': req_id, 'status': status})

async def close():
    await connection.close()
