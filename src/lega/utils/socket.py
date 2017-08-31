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
import os
from syslog import syslog, LOG_DEBUG, LOG_INFO, LOG_WARNING
import argparse
import asyncio
import ssl
from functools import partial
from pathlib import Path
import socket

CHUNK_SIZE=4096

# Monkey-patching ssl
ssl.match_hostname = lambda cert, hostname: True

LISTEN_FDS = int(os.environ.get("LISTEN_FDS", 0))
#LISTEN_PID = os.environ.get("LISTEN_PID", None) or os.getpid()

async def copy_chunk(reader,writer):
    while True:
        data = await reader.read(CHUNK_SIZE)
        if not data:
            return
        #syslog(LOG_DEBUG,f'DATA: {data}')
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

    socket_path = Path(args.socket).expanduser()
    certfile = Path(args.certfile).expanduser() if args.certfile else None

    syslog(LOG_INFO, f'Socket: {socket_path}')
    syslog(LOG_INFO, f'Remote machine: {args.remote_machine}')
    syslog(LOG_DEBUG, f'Certfile: {certfile}')

    if args.chunk:
        CHUNK_SIZE = args.chunk
        syslog(LOG_INFO, f'Chunk size: {args.chunk}')

    ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=certfile) if (certfile and certfile.exists()) else None

    if not ssl_ctx:
        syslog(LOG_WARNING, 'No SSL encryption')
    else:
        syslog(LOG_INFO, 'With SSL encryption')

    host,port = args.remote_machine.split(':')

    if LISTEN_FDS == 0:
        _sock = None
    else: # reuse the socket from systemd
        socket_path=None
        _sock=socket.fromfd(3, socket.AF_UNIX, socket.SOCK_STREAM, proto=0)

    loop = asyncio.get_event_loop()
    connection_factory = lambda : asyncio.open_connection(host=host,
                                                          port=int(port),
                                                          ssl=ssl_ctx)
    server = loop.run_until_complete(
        asyncio.start_unix_server(partial(handle_connection,connection_factory),
                                  path=socket_path, # re-created if stale
                                  sock=_sock,
                                  loop=loop)
    )
    try:
        loop.run_forever()
    except Exception as e:
        syslog(LOG_DEBUG, repr(e))
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

    syslog(LOG_INFO, f'Remote: {args.address}')
    syslog(LOG_INFO, f'Socket: {args.socket}')

    if args.chunk:
        CHUNK_SIZE = args.chunk
        syslog(LOG_INFO, f'Chunk size: {args.chunk}')

    ssl_ctx = None
    certfile = Path(args.certfile).expanduser() if args.certfile else None
    keyfile = Path(args.keyfile).expanduser() if args.keyfile else None
    syslog(LOG_DEBUG, f'Certfile: {certfile}')
    syslog(LOG_DEBUG, f'Keyfile: {keyfile}')
    if (certfile and certfile.exists() and 
        keyfile and keyfile.exists()):
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile, keyfile)

    if not ssl_ctx:
        syslog(LOG_WARNING, 'No SSL encryption')
    else:
        syslog(LOG_INFO, 'With SSL encryption')

    address,port = args.address.split(':')
    if LISTEN_FDS == 0:
        socket_path = args.socket
        _sock = None
    else: # reuse the socket from systemd
        socket_path = None
        _sock=socket.fromfd(3, socket.AF_UNIX, socket.SOCK_STREAM, proto=0)

    loop = asyncio.get_event_loop()
    connection_factory = lambda : asyncio.open_unix_connection(path=socket_path, sock=_sock)
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
        syslog(LOG_DEBUG, repr(e))
        server.close()
    
    loop.close()
