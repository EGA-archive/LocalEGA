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
import yaml

from aiohttp import web, TCPConnector, ClientSession
import jinja2
import aiohttp_jinja2

# For the match, we turn that off
ssl.match_hostname = lambda cert, hostname: True

LOG = logging.getLogger('cega-server')

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
    users_dir = Path(__file__).parent / 'users'
    files = [f for f in users_dir.iterdir() if f.is_file()]
    users = {}
    for f in files:
        with open(f, 'r') as stream:
            users[f.stem] = yaml.load(stream)
    return { "users": users }

async def user(request):
    name = request.match_info['id']
    LOG.info(f'Getting info for user: {name}')
    try:
        with open(f'users/{name}.yml', 'r') as stream:
            d = yaml.load(stream)
        json_data = { 'password_hash': d.get("password_hash",None), 'pubkey': d.get("pubkey",None), 'expiration': d.get("expiration",None) }
        return web.json_response(json_data)
    except OSError:
        raise web.HTTPBadRequest(text=f'No info for that user {name}... yet\n')

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

