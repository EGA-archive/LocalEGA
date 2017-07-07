#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Catching the gpg request by reading the gpg-agent socket,
encrypting the message and sending them to the machine running the
gpg-agent.

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.

'''

import sys
import os
import logging
import socket
from pathlib import Path

from .conf import CONF

LOG = logging.getLogger('gpg_requester')

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    gpg_socket = Path( CONF.get('worker','gpg_home') ) / 'S.gpg-agent'
    LOG.info(f'GPG socket: {gpg_socket}')

    # Re-create the socket if already exists
    if gpg_socket.exists():
        LOG.info('Removing it, as it already exists')
        gpg_socket.unlink()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0) as s:

        LOG.debug('Binding')
        s.bind(str(gpg_socket))
        s.listen(1) # Accepting one client
        gpg_socket.chmod(0o700)

        while True:
            conn, addr = s.accept()
            with conn:
                LOG.debug(f'Connection on {conn.getsockname()} (fileno {conn.fileno()})')

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as gpg:
                    LOG.debug(f'Connecting to ega-keys')
                    gpg.connect(('ega-keys',9010))
                    bits = []
                    while True:
                        data = conn.recv(8192)
                        if not data:
                            break
                        bits.append(data)
                    msg = b''.join(bits)
                    LOG.debug(msg)
                    gpg.sendall(msg)

                LOG.debug(f'Connection to ega-keys closed')
            

if __name__ == '__main__':
    main()

