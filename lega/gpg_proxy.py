#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GPG agent multiplexer.
It accepts many requests and forwards them to the running gpg-agent.
The answer is redirected back to the incoming connection.

If we find the need, the message can be encrypted (see `copy_chunk`).

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
#import ssl

from .conf import CONF

LOG = logging.getLogger('gpg_proxy')

async def copy_chunk(reader,writer,process=None):
    while True:
        data = await reader.read(4096)
        if not data:
            return
        if process: # Decrypt and Encrypt the data?
            data=process(data)
        writer.write(data)
        await writer.drain()

async def handle_connection(gpg_socket_path, reader_conn,writer_conn):

    name_from = writer_conn.get_extra_info('peername')
    LOG.debug(f'Connection to {name_from}')

    reader_agent, writer_agent = await asyncio.open_unix_connection(path=gpg_socket_path)

    await asyncio.gather(
        copy_chunk(reader_conn,writer_agent),
        copy_chunk(reader_agent,writer_conn)
    )
    writer_conn.close()
    writer_agent.close()

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    loop = asyncio.get_event_loop()
    gpg_socket_path = Path( CONF.get('worker','gpg_home') ) / 'S.gpg-agent.extra'
    LOG.info(f'GPG socket: {gpg_socket_path}')

    server = loop.run_until_complete(
        asyncio.start_server(partial(handle_connection,str(gpg_socket_path)),
                             host='0.0.0.0',
                             port=9010,
                             #ssl=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH),
                             loop=loop)
    )
    try:
        loop.run_forever()
    except Exception as e:
        LOG.debug(repr(e))
        server.close()
    
    loop.close()


# def copy_socket(from_socket,to_socket,size):
#     while True:
#         LOG.debug(f'Receiving data from {from_socket.getsockname()}')
#         data = from_socket.recv(size)
#         if not data:
#             break
#         LOG.debug(f'Data: {data}')
#         LOG.debug(f'Resending data to {from_socket.getsockname()}')
#         to_socket.send(data)

# def main(args=None):

#     if not args:
#         args = sys.argv[1:]

#     CONF.setup(args) # re-conf

#     gpg_socket_path = Path.home() / '.gnupg' / 'S.gpg-agent.extra'
#     gpg_socket_path.chmod(0o700)
#     LOG.info(f'Connection {gpg_socket_path}')
#     gpg = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
#     gpg.connect(str(gpg_socket_path))

#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     rcvbuf_size = s.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.bind( ('0.0.0.0', 9010) )
#     s.listen(1)

#     try:
#         while True:
#             conn, addr = s.accept()
#             with conn:
#                 LOG.debug(f'Connection on {conn.getsockname()} (fileno {conn.fileno()})')

#                 listen = threading.Thread(group=None, target=copy_socket, args=(conn,gpg, rcvbuf_size))
#                 echo = threading.Thread(group=None, target=copy_socket, args=(gpg,conn, 8192))

#                 listen.start()
#                 echo.start()

#                 listen.join()
#                 echo.join()
                
#             #conn.close(), closed by context manager
#     finally:
#         gpg.close()
#         s.close()

if __name__ == '__main__':
    main()

