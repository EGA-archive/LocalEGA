#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test server to act as CentralEGA endpoint for users

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import os
import logging
import asyncio
from pathlib import Path
from functools import wraps
import ssl

from aiohttp import web, TCPConnector, ClientSession
import jinja2
import aiohttp_jinja2

# For the match, we turn that off
ssl.match_hostname = lambda cert, hostname: True

LOG = logging.getLogger('cega-server')

_USERS = {
    "fred": { 'password_hash': "$1$xyz$sx8gPI05DJdJe4MJx5oXo0", "expiration": "1 month", "pubkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCyKoPimxBFwUYx1SDYZMV8x/IVdisShv0kvcJ3SRXny5vR7wTGU1gz6jaoM1mG+i+5NszJKxsEj4/HXHYVcOWithVw81cLuaA4nlSlQEwLqgPSBkUvRV29BHaeIBsbNY9pJOOr/PczTo5gKMFER69VbNmwixVHyAtngZdMjdcp0PezbKQ3xmSmYuKH5+CKzx69r/saEyoLLr5enQ0KkJJyNyVQRZb0Qoxjz0Qtno0c0NJzm8ivLp9G6y0p+/aQ/K/BUhsIgwgY5aSEePTU2iQ4tibgVu/1+XR7Y+7F9PIEXcQ6tLRQTQPLNx1ikZy3lWqKNOU2Dp9nR0QU69LUjEVN8jKjiOIu83KMIUZgFFmTZB4VoppjLZey1pIQuUeiXrxQcMKnOMRabHgh3M0bzlEwUVOD2jspSlLooE4J4gh4EMmCCvDwawe2pkBJMfZYk2nyWQDDiFpazQvEKBg5QW/WLvMLOPfpeEdNJLj6HRARAJaDhIcXFxIaDLmVDaoOUlUN9padxFNQtIWnw/yE8livGSNPM3DSGJ+/fZCQQouvWlppg4kV8HDt/NwMwPUqnWXy++tNbpo2QxPeyCcA6lruRaq944aO+9rafnuWYC6coUmJNoCoNmuB3W1aeeAsuoJx0zt0LhVG/L3/Ea3fQDmECMXPArutX2j37q4E8xMiFw== daz.admin@lega.sftp" },
    "juha": { 'password_hash': "$1$xyz$OcPwHHMV7Y2fEaYljaqOX/", "expiration": "INTERVAL '3' MONTH" },
    "santa": { 'password_hash': "$1$xyz$BuJSZKSSNzxpx1.erEcp21", },
}

def only_central_ega(async_func):
    '''Decorator restrain endpoint access to only Central EGA'''
    @wraps(async_func)
    async def wrapper(request):
        # Just an example
        if request.headers.get('X-CentralEGA', 'no') != 'yes':
            raise web.HTTPUnauthorized(text='Not authorized. You should be Central EGA.\n')
        # Otherwise, it is from CentralEGA, we continue
        res = async_func(request)
        res.__name__ = getattr(async_func, '__name__', None)
        res.__qualname__ = getattr(async_func, '__qualname__', None)
        return (await res)
    return wrapper


@aiohttp_jinja2.template('users.html')
async def index(request):
    '''Main endpoint with documentation

    The template is `index.html` in the configured template folder.
    '''
    return { "users": _USERS }

async def user(request):
    name = request.match_info['id']
    LOG.info(f'Getting info for user: {name}')
    res = _USERS.get(name, None)
    if not res:
        raise web.HTTPBadRequest(text=f'No info for that user {name}... yet\n')
    json_data = { 'password_hash': res.get("password_hash",None), 'pubkey': res.get("pubkey",None), 'expiration': res.get("expiration",None) }
    return web.json_response(json_data)

async def cleanup(app):
    '''Function run after a KeyboardInterrupt. Right after, the loop is closed'''
    LOG.info('Cancelling all pending tasks')
    for task in asyncio.Task.all_tasks():
        task.cancel()

def main(args=None):

    loop = asyncio.get_event_loop()
    server = web.Application(loop=loop)

    # Where the templates are
    template_loader = jinja2.FileSystemLoader(".")
    aiohttp_jinja2.setup(server, loader=template_loader)

    # Registering the routes
    LOG.info('Registering routes')
    server.router.add_get( '/'         , index, name='root')
    server.router.add_get( '/user/{id}', user , name='user')

    # Registering some initialization and cleanup routines
    LOG.info('Setting up callbacks')
    server.on_cleanup.append(cleanup)

    # LOG.info('Preparing SSL context')
    # ssl_ctx = ssl.create_default_context(cafile='certs/ca.cert.pem')
    # ssl_ctx.load_cert_chain('certs/cega.cert.pem', 'private/cega.key.pem', password="hello")
    ssl_ctx = None

    # And ...... cue music!
    host="0.0.0.0"
    port=9100
    LOG.info(f'Starting the real deal on <{host}:{port}>')
    web.run_app(server, host=host, port=port, shutdown_timeout=0, ssl_context=ssl_ctx)
    # https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web.py
    # run_app already catches the KeyboardInterrupt and calls loop.close() at the end

    LOG.info('Exiting the frontend')


if __name__ == '__main__':
    main()

