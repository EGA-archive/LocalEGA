#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import asyncio
import ssl
from pathlib import Path

from .conf import CONF, KeysConfiguration
from .utils import get_file_content

LOG = logging.getLogger('keyserver')

PGP_SECKEY        = b'1'
PGP_PUBKEY        = b'2'
PGP_PASSPHRASE    = b'3'
MASTER_SECKEY     = b'4'
MASTER_PUBKEY     = b'5'
MASTER_PASSPHRASE = b'6'

# For the match, we turn that off
ssl.match_hostname = lambda cert, hostname: True

async def _req(req, host, port, ssl=None, loop=None):
    reader, writer = await asyncio.open_connection(host, port, ssl=ssl, loop=loop)

    try:
        LOG.info(f"Sending request for {req}")
        # What does the client want
        writer.write(req)
        await writer.drain()

        LOG.info("Waiting for answer")
        buf=bytearray()
        while True:
            data = await reader.read(1000)
            if data:
                buf.extend(data)
            else:
                writer.close()
                LOG.info("Got it")
                return buf
    except Exception as e:
        LOG.error(repr(e))
        writer.write(repr(e))
        await writer.drain()
        writer.close()

def get_ingestion_keys(host, port, ssl):
    loop = asyncio.get_event_loop()
    pgp_private_keyblob = loop.run_until_complete(_req(PGP_SECKEY, host, port, ssl=ssl, loop=loop))
    pgp_passphrase = loop.run_until_complete(_req(PGP_PASSPHRASE, host, port, ssl=ssl, loop=loop))
    master_public_keyblob = loop.run_until_complete(_req(MASTER_PUBKEY, host, port, ssl=ssl, loop=loop))
    loop.close()
    # Can be a bytearray
    return pgp_private_keyblob, pgp_passphrase.decode(), master_public_keyblob


class KeysProtocol(asyncio.Protocol):

    def __init__(self, secrets):
        self.transport = None
        self._secrets = secrets

    def connection_made(self, transport: asyncio.Transport):
        LOG.info("Start connection")
        self.transport = transport

    def data_received(self, data: bytes):
        s = self._secrets.get(data, None)
        if s:
            LOG.info(f'Sending secret over for {data}')
            self.transport.write(s)
        else:
            LOG.error(f'Unknown secret for {data}')
            self.transport.write('ERROR')
        self.transport.close() # We're done

    def connection_lost(self, exc):
        LOG.info("Closing connection")


def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf
    KEYS = KeysConfiguration(args)

    # Those settings must exist. Crash otherwise.
    ssl_certfile = Path(CONF.get('keyserver','ssl_certfile')).expanduser()
    ssl_keyfile = Path(CONF.get('keyserver','ssl_keyfile')).expanduser()
    LOG.debug(f'Certfile: {ssl_certfile}')
    LOG.debug(f'Keyfile: {ssl_keyfile}')

    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(ssl_certfile, ssl_keyfile)

    if not ssl_ctx:
        LOG.error('No SSL encryption. Exiting...')
        sys.exit(2)
    else:
        LOG.info('With SSL encryption')

    # PGP Private Key
    active_pgp_key = KEYS.getint('DEFAULT','active_pgp_key')
    pgp_seckey = get_file_content(KEYS.get(f'pgp.key.{active_pgp_key}','seckey'))
    pgp_pubkey = get_file_content(KEYS.get(f'pgp.key.{active_pgp_key}','pubkey'))
    pgp_passphrase = (KEYS.get(f'pgp.key.{active_pgp_key}','passphrase')).encode()

    # Active Public Master Key
    active_master_key = KEYS.getint('DEFAULT','active_master_key')
    master_seckey = get_file_content(KEYS.get(f'master.key.{active_master_key}','seckey'))
    master_pubkey = get_file_content(KEYS.get(f'master.key.{active_master_key}','pubkey'))
    master_passphrase = (KEYS.get(f'master.key.{active_master_key}','passphrase')).encode()

    secrets = {
        PGP_SECKEY        : pgp_seckey,
        PGP_PUBKEY        : pgp_pubkey,
        PGP_PASSPHRASE    : pgp_passphrase,
        MASTER_SECKEY     : master_seckey,
        MASTER_PUBKEY     : master_pubkey,
        MASTER_PASSPHRASE : master_passphrase,
    }

    keys_protocol = KeysProtocol(secrets)

    host = CONF.get('keyserver','host')
    port = CONF.getint('keyserver','port')
    loop = asyncio.get_event_loop()
 
    server = loop.run_until_complete(
        loop.create_server(lambda : keys_protocol, # each connection use that object
                           host=host,
                           port=port,
                           ssl=ssl_ctx)
    )
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        LOG.debug(repr(e))
    
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

if __name__ == '__main__':
    main()
