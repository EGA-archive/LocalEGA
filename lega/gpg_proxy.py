#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GPG agent multiplexer.
It accepts many requests and forwards them to the running gpg-agent

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import os
import logging
import asyncio
import socket
from pathlib import Path
from functools import partial

from .conf import CONF

LOG = logging.getLogger('gpg_multiplexer')

async def handle_request(gpg_socket, reader, writer):

    addr = writer.get_extra_info('peername')
    LOG.debug(f"Handle request from {addr!r}")

    bits = []
    while True:
        data = await reader.read(8192)
        bits.append(data)

    message = ''.join(bits)
    LOG.debug(f"Received {message.decode()}")
    gpg_socket.write(message)

    while True:
        rdata = gpg_socket.recv(8192)
        writer.write(rdata)
        await writer.drain()
        if not rdata:
            break

    LOG.debug("Close the client socket")
    writer.close()

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    LOG.info('Starting')
    loop = asyncio.get_event_loop()
    gpg_socket_path = Path.home() / '.gnupg' / 'S.gpg-agent'

    LOG.info(f'Connecting to {gpg_socket_path}')
    gpg_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        gpg_socket.connect(str(gpg_socket_path))
    except socket.error as e:
        LOG.error(e)
        sys.exit(1)

    coro = asyncio.start_server(partial(handle_request, gpg_socket),
                                host='0.0.0.0',
                                port=9010,
                                loop=loop)
    server = loop.run_until_complete(coro)
    
    # Serve requests until Ctrl+C is pressed
    LOG.info('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
    LOG.info('Over and Out')

if __name__ == '__main__':
    main()

