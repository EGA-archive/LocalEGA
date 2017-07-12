#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Catching the gpg request by reading the gpg-agent socket,
and sending them to the machine running the gpg-agent.

If we find the need, the message can be encrypted (see `copy_chunk`).

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.

'''

import sys
import logging
import asyncio
#import ssl

from .conf import CONF

LOG = logging.getLogger('gpg_forwarder')

async def copy_chunk(reader,writer,process=None):
    while True:
        data = await reader.read(4096)
        if not data:
            return
        if process: # Decrypt and Encrypt the data?
            data=process(data)
        writer.write(data)
        await writer.drain()

async def handle_connection(reader_gpg,writer_gpg):

    name_from = writer_gpg.get_extra_info('sockname')
    LOG.debug(f'Connection to {name_from}')

    reader_agent, writer_agent = await asyncio.open_connection(host='ega-keys',
                                                               port=9010) #ssl=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    name_to = writer_agent.get_extra_info('peername')
    LOG.debug(f'Connection to {name_to}')

    await asyncio.gather(
        copy_chunk(reader_agent,writer_gpg),
        copy_chunk(reader_gpg,writer_agent)
    )
    writer_gpg.close()
    writer_agent.close()

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    loop = asyncio.get_event_loop()
    gpg_socket_path = CONF.get('worker','gpg_home') + '/S.gpg-agent'
    LOG.info(f'GPG socket: {gpg_socket_path}')

    server = loop.run_until_complete(
        asyncio.start_unix_server(handle_connection,
                                  path=gpg_socket_path, # re-created if stale
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

