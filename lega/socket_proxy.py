#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GPG agent multiplexer.
It accepts many requests and forwards them to the running gpg-agent.
The answer is redirected back to the incoming connection.

The traffic goes through an SSL connection.

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import logging
import asyncio
import ssl
from functools import partial
import argparse
from pathlib import Path

LOG = logging.getLogger('socket_proxy')

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

async def handle_connection(socket_path, reader_conn,writer_conn):

    name_from = writer_conn.get_extra_info('peername')
    LOG.debug(f'Connection to {name_from}')

    reader_agent, writer_agent = await asyncio.open_unix_connection(path=socket_path)

    await asyncio.gather(
        copy_chunk(reader_conn,writer_agent),
        copy_chunk(reader_agent,writer_conn)
    )
    writer_conn.close()
    writer_agent.close()

def main():

    global CHUNK_SIZE

    parser = argparse.ArgumentParser(description='Forward a socket to a remote machine', allow_abbrev=False)
    parser.add_argument('address', help='Binding to <addr:port>')
    parser.add_argument('socket', help='Socket location')
    parser.add_argument('--certfile', help='Certificat for SSL communication')
    parser.add_argument('--keyfile', help='Private key for SSL communication')
    parser.add_argument('--chunk', help='Size of the chunk to forward. [Default: 4096]', type=int)
    args = parser.parse_args()

    LOG.info(f'Remote: {args.address}')
    LOG.info(f'Socket: {args.socket}')

    if args.chunk:
        CHUNK_SIZE = args.chunk
        LOG.info(f'Chunk size: {args.chunk}')

    ssl_ctx = None
    if (args.certfile and Path(args.certfile).exists() and 
        args.keyfile and Path(args.keyfile).exists()):
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(args.certfile, args.keyfile)

    if not ssl_ctx:
        LOG.warning('No SSL encryption')

    address,port = args.address.split(':')

    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(
        asyncio.start_server(partial(handle_connection,args.socket),
                             host=address,
                             port=port,
                             ssl=ssl_ctx,
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

