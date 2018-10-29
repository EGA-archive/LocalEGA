#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Checking permissions for a given stable ID.
#
# ... and forwarding to the re-encryption streamer
#
####################################
'''

import sys
import logging
import ssl
from pathlib import Path
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from aiohttp import web, ClientSession, ClientTimeout

from .conf import CONF, configure

LOG = logging.getLogger(__name__)

async def outgest(r):
    # Get token from header
    auth = r.headers.get('Authorization')
    if not auth.lower().startswith('bearer '):
        raise web.HTTPBadRequest(reason='Invalid request')
    access_token = auth[7:]
    LOG.debug('Access Token from header: %s', access_token)
    if not access_token:
        LOG.error('Invalid Access: Missing access_token')
        raise web.HTTPBadRequest(reason='Invalid Request')

    # Get POST data and check it
    data = await r.post()
    stable_id = data.get('stable_id')
    if not stable_id:
        LOG.error('Invalid Request: Missing stable ID')
        raise web.HTTPBadRequest(reason='Invalid Request')
    # method = data.get('method')
    # if not method:
    #     LOG.error('Invalid Request: Missing reencryption method')
    #     raise web.HTTPBadRequest(reason='Invalid Request')
    pubkey = data.get('pubkey')
    if not pubkey:
        LOG.error('Invalid Request: Missing public key for reencryption')
        raise web.HTTPBadRequest(reason='Invalid Request')

    # Check now Permissions, for that stable_id. If 200 OK, then granted
    permissions_url = r.app['permissions_url'] % stable_id

    async with ClientSession() as session:
        LOG.debug('POST Request: %s', permissions_url)
        async with session.request('GET',
                                   permissions_url,
                                   headers={ 'Authorization': auth, # same as above
                                             'Accept': 'application/json',
                                             'Cache-Control': 'no-cache' }) as response:
            if response.status > 200:
                LOG.error("Invalid permissions for stable_id %s [status: %s]", stable_id, response.status)
                raise web.HTTPBadRequest(text='Invalid request')

    # Valid Permissions: Forward to Re-Encryption
    LOG.info("Valid Request and Permissions: Forwarding to Re-Encryption Streamer")
    streamer_url = CONF.get_value('outgestion', 'streamer_endpoint')
    timeout = ClientTimeout(total=CONF.get_value('outgestion', 'timeout', conv=int, default=300))
    async with ClientSession(timeout=timeout) as session:
        LOG.debug('POST Request: %s', streamer_url)
        async with session.request('POST',
                                   streamer_url,
                                   headers={ 'Content-Type': 'application/json' },
                                   json={ 'stable_id': stable_id,
                                          'pubkey': pubkey,
                                          'client_ip': r.remote }) as response:

            LOG.debug('Response: %s', response)
            LOG.debug('Response type: %s', response.headers.get('CONTENT-TYPE'))
            if response.status > 200:
                raise web.HTTPBadRequest(reason=f'HTTP status code: {response.status}')

            # Ready to answer
            resp = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'application/octet-stream'})
            await resp.prepare(r)
            # Forwarding the content
            while True:
                chunk = await response.content.read(1<<22) # 4 MB
                if not chunk:
                    break
                await resp.write(chunk)
                await resp.drain()

            # Finally
            await resp.write_eof()
            return resp

@configure
def main():

    host = CONF.get_value('outgestion', 'host')  # fallbacks are in defaults.ini
    port = CONF.get_value('outgestion', 'port', conv=int)

    sslcontext = None
    if CONF.get_value('outgestion', 'enable_ssl', conv=bool, default=True):
        ssl_certfile = Path(CONF.get_value('outgestion', 'ssl_certfile')).expanduser()
        ssl_keyfile = Path(CONF.get_value('outgestion', 'ssl_keyfile')).expanduser()
        LOG.debug(f'Certfile: {ssl_certfile}')
        LOG.debug(f'Keyfile: {ssl_keyfile}')
        sslcontext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        sslcontext.check_hostname = False
        sslcontext.load_cert_chain(ssl_certfile, ssl_keyfile)

    #loop = asyncio.get_event_loop()
    #loop.set_debug(True)

    server = web.Application()
    server.router.add_post('/', outgest) 

    # Initialization
    server['permissions_url'] = CONF.get_value('outgestion', 'permissions_endpoint', raw=True)

    LOG.info(f"Start outgest server on {host}:{port}")
    web.run_app(server, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
