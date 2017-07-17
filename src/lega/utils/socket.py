#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Unix Domain Socket forwarding to remote machine and 
proxying remote requests to a given Unix Domain Socket.

Usefull to forward gpg requests to a remote GPG-agent.

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

LOG = logging.getLogger('socket-forwarder')

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

async def handle_connection(connection_factory, reader_from,writer_from):

    reader_to, writer_to = await connection_factory()

    await asyncio.gather(
        copy_chunk(reader_from,writer_to),
        copy_chunk(reader_to,writer_from)
    )

    writer_from.close()
    writer_to.close()

def forward():
    '''
    Catching the traffic on a socket,
    and sending it to a remote machine.
    
    The traffic goes through an SSL connection.
    
    Useful to forward a local gpg request onto a remote gpg-agent.
    '''

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
    connection_factory = lambda : asyncio.open_connection(host=host,
                                                          port=int(port),
                                                          ssl=ssl_ctx)
    server = loop.run_until_complete(
        asyncio.start_unix_server(partial(handle_connection,connection_factory),
                                  path=args.socket, # re-created if stale
                                  loop=loop)
    )
    try:
        loop.run_forever()
    except Exception as e:
        LOG.debug(repr(e))
        server.close()
    
    loop.close()

def proxy():
    '''
    Socket multiplexer.

    It accepts many requests and forwards them to the given socket.
    The answer is redirected back to the incoming connection.
    
    The traffic goes through an SSL connection.
    
    Used to multiplex the gpg-agent.
    '''

    global CHUNK_SIZE

    parser = argparse.ArgumentParser(description='Forward a socket to a remote machine', allow_abbrev=False)
    parser.add_argument('address', help='Binding to <addr:port>')
    parser.add_argument('socket', help='Socket location')
    parser.add_argument('--certfile', help='Certificat for SSL communication')
    parser.add_argument('--keyfile', help='Private key for SSL communication')
    parser.add_argument('--chunk', help=f'Size of the chunk to forward. [Default: {CHUNK_SIZE}]', type=int)
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
    connection_factory = lambda : asyncio.open_unix_connection(path=socket_path)
    server = loop.run_until_complete(
        asyncio.start_server(partial(handle_connection,connection_factory),
                             host=address,
                             port=int(port),
                             ssl=ssl_ctx,
                             loop=loop)
    )
    try:
        loop.run_forever()
    except Exception as e:
        LOG.debug(repr(e))
        server.close()
    
    loop.close()
