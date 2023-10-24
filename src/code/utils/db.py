import sys
import logging
import asyncio
import json
from socket import gethostname
from pwd import getpwuid
import os
import ssl

import asyncpg
import pamqp
from yarl import URL

LOG = logging.getLogger(__name__)

class DBConnection():
    """ Connection abstraction """

    __slots__ = (
        'connection',
        'conf',
        'conf_section'
    )

    def __init__(self, conf, conf_section='db'):
        self.connection = None
        self.conf = conf
        self.conf_section = conf_section
        
    def __str__(self):
        return str(self.connection) if self.connection else self.__class__.__name__

    def __repr__(self):
        return '<{0}: "{1}">'.format(self.__class__.__name__, str(self))

    async def connect(self):
        LOG.debug('Getting the DB connection configuration')
        dsn = self.conf.getsensitive(self.conf_section, 'connection', raw=True)
        if not dsn:
            raise Exception(f'Invalid configuration in section [{self.conf_section}]')
        if isinstance(dsn, bytes):  # secret to str
            dsn = dsn.decode()

        LOG.debug('Creating the DB connection pool')
        self.connection = await asyncpg.create_pool(dsn)
        #LOG.info('Connection to %s', self.connection.url.with_password('****'))
        await self.connection.execute('SELECT 1') # ping

    async def dataset_mapping(self, *args, **kwargs):

        query = self.conf.get(self.conf_section, 'dataset_mapping', raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def dataset_release(self, *args, **kwargs):

        query = self.conf.get(self.conf_section, 'dataset_release', raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def dataset_deprecated(self, *args, **kwargs):

        query = self.conf.get(self.conf_section, 'dataset_deprecated', raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def dataset_permission(self, *args, **kwargs):

        query = self.conf.get(self.conf_section, 'dataset_permission', raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def dataset_delete_permission(self, *args, **kwargs):

        query = self.conf.get(self.conf_section, 'dataset_delete_permission', raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def save_dac(self, *args, **kwargs):

        query = self.conf.get(self.conf_section, 'dac_query', raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def save_file(self, *args, **kwargs):

        query = self.conf.get(self.conf_section, 'save_query', raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def fetchval(self, stmt, *args, **kwargs):

        query = self.conf.get(self.conf_section, stmt, raw=True)
        if not query:
            raise Exception('Invalid Vault DB configuration')

        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args, **kwargs)

    async def ping(self):
        LOG.debug('Pinging the DB')

        if not self.connection:
            await self.connect()

        return await self.connection.execute('SELECT 1')
