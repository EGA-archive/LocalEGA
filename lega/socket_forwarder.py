#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Catching the traffic on a socket,
and sending it to a remote machine.

The traffic goes through an SSL connection.

Useful to forward a local gpg request onto a remote gpg-agent.

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.

'''

import sys
import logging
import argparse
import asyncio
import ssl
from functools import partial
from pathlib import Path

LOG = logging.getLogger('socket_forwarder')

CHUNK_SIZE=4096

# Monkey-patching ssl
ssl.match_hostname = lambda cert, hostname: True

async def copy_chunk(reader,writer):
    while True:
        data = await reader.read(CHUNK_SIZE)
        if not data:
            return
        writer.write(data)
        await writer.drain()

async def handle_connection(host,port,ssl_ctx, reader_gpg,writer_gpg):

    name_from = writer_gpg.get_extra_info('sockname')
    LOG.debug(f'Connection to {name_from}')

    reader_agent, writer_agent = await asyncio.open_connection(host=host,
                                                               port=port,
                                                               ssl=ssl_ctx)

    name_to = writer_agent.get_extra_info('peername')
    LOG.debug(f'Connection to {name_to}')

    await asyncio.gather(
        copy_chunk(reader_agent,writer_gpg),
        copy_chunk(reader_gpg,writer_agent)
    )
    writer_gpg.close()
    writer_agent.close()

def main():

    global CHUNK_SIZE

    parser = argparse.ArgumentParser(description='Forward a socket to a remote machine', allow_abbrev=False)
    parser.add_argument('socket', help='Socket location')
    parser.add_argument('remote_machine', help='Remote location <host:port>')
    parser.add_argument('--certfile', help='Certificat for SSL communication')
    parser.add_argument('--chunk', help='Size of the chunk to forward. [Default: 4096]', type=int)
    args = parser.parse_args()

    LOG.info(f'Socket: {args.socket}')
    LOG.info(f'Remote machine: {args.remote_machine}')

    if args.chunk:
        CHUNK_SIZE = args.chunk
        LOG.info(f'Chunk size: {args.chunk}')

    ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, 
                                         cafile=args.certfile) if (args.certfile and Path(args.certfile).exists()) else None

    if not ssl_ctx:
        LOG.warning('No SSL encryption')

    host,port = args.remote_machine.split(':')

    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(
        asyncio.start_unix_server(partial(handle_connection,host,port,ssl_ctx),
                                  path=args.socket, # re-created if stale
                                  loop=loop)
    )
    try:
        loop.run_forever()
    except Exception as e:
        LOG.debug(repr(e))
        server.close()
    
    loop.close()

if __name__ == '__main__':
    main()

