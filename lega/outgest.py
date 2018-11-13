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
import ssl
from pathlib import Path
import uuid
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from aiohttp import web, ClientSession, ClientTimeout

from .conf import CONF, configure
from .utils.logging import LEGALogger

LOG = LEGALogger(__name__)

async def outgest(r):

    correlation_id = str(uuid.uuid4())

    # Get token from header
    auth = r.headers.get('Authorization')
    if not auth.lower().startswith('bearer '):
        raise web.HTTPBadRequest(reason='Invalid request')
    access_token = auth[7:]
    LOG.debug('Access Token from header: %s', access_token, extra={'correlation_id': correlation_id})
    if not access_token:
        LOG.error('Invalid Access: Missing access_token', extra={'correlation_id': correlation_id})
        raise web.HTTPBadRequest(reason='Invalid Request')

    # Get POST data and check it
    data = await r.post()
    stable_id = data.get('stable_id')
    if not stable_id:
        LOG.error('Invalid Request: Missing stable ID', extra={'correlation_id': correlation_id})
        raise web.HTTPBadRequest(reason='Invalid Request')
    # method = data.get('method')
    # if not method:
    #     LOG.error('Invalid Request: Missing reencryption method', extra={'correlation_id': correlation_id})
    #     raise web.HTTPBadRequest(reason='Invalid Request')
    pubkey = data.get('pubkey')
    if not pubkey:
        LOG.error('Invalid Request: Missing public key for reencryption', extra={'correlation_id': correlation_id})
        raise web.HTTPBadRequest(reason='Invalid Request')

    # Check now Permissions, for that stable_id. If 200 OK, then granted
    permissions_url = r.app['permissions_url'] % stable_id

    async with ClientSession() as session:
        LOG.debug('POST Request: %s', permissions_url, extra={'correlation_id': correlation_id})
        async with session.request('GET',
                                   permissions_url,
                                   headers={ 'Authorization': auth, # same as above
                                             'Accept': 'application/json',
                                             'Cache-Control': 'no-cache',
                                             'correlation_id': correlation_id
                                   }) as response:
            if response.status > 200:
                LOG.error("Invalid permissions for stable_id %s [status: %s]",
                          stable_id, response.status,
                          extra={'correlation_id': correlation_id})
                raise web.HTTPBadRequest(text='Invalid request')

    # Valid Permissions: Forward to Re-Encryption
    LOG.info("Valid Request and Permissions: Forwarding to Re-Encryption Streamer", extra={'correlation_id': correlation_id})
    streamer_url = CONF.get_value('DEFAULT', 'streamer_endpoint')
    timeout = ClientTimeout(total=CONF.get_value('DEFAULT', 'timeout', conv=int, default=300))
    async with ClientSession(timeout=timeout) as session:
        LOG.debug('POST Request: %s', streamer_url, extra={'correlation_id': correlation_id})
        async with session.request('POST',
                                   streamer_url,
                                   headers={
                                       'Content-Type': 'application/json',
                                       'correlation_id': correlation_id
                                   },
                                   json={ 'stable_id': stable_id,
                                          'pubkey': pubkey,
                                          'client_ip': r.remote }) as response:

            LOG.debug('Response: %s', response, extra={'correlation_id': correlation_id})
            LOG.debug('Response type: %s', response.headers.get('CONTENT-TYPE'), extra={'correlation_id': correlation_id})
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

    host = CONF.get_value('DEFAULT', 'host')
    port = CONF.get_value('DEFAULT', 'port', conv=int)

    sslcontext = None
    if CONF.get_value('DEFAULT', 'enable_ssl', conv=bool, default=True):
        ssl_certfile = Path(CONF.get_value('DEFAULT', 'ssl_certfile')).expanduser()
        ssl_keyfile = Path(CONF.get_value('DEFAULT', 'ssl_keyfile')).expanduser()
        LOG.debug('Certfile: %s', ssl_certfile, extra={'correlation_id': correlation_id})
        LOG.debug('Keyfile: %s', ssl_keyfile, extra={'correlation_id': correlation_id})
        sslcontext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        sslcontext.check_hostname = False
        sslcontext.load_cert_chain(ssl_certfile, ssl_keyfile)

    #loop = asyncio.get_event_loop()
    #loop.set_debug(True)

    server = web.Application()
    server.router.add_post('/', outgest) 

    # Initialization
    server['permissions_url'] = CONF.get_value('DEFAULT', 'permissions_endpoint', raw=True)

    LOG.info(f"Start outgest server on {host}:{port}")
    web.run_app(server, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
