#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Ingestion API Front-end
#
####################################

We provide:

|-----------------------------------|------------|----------------------------------------|
| endpoint                          | method     | Notes                                  |
|-----------------------------------|------------|----------------------------------------|
| [LocalEGA-URL]/                   | GET        | Frontpage                              |
| [LocalEGA-URL]/file?user=&name=   | GET        | Information on a file for a given user |
| [LocalEGA-URL]/user/<name>        | GET        | JSON array of all files information    |
| [LocalEGA-URL]/user/<name>        | DELETE     | Revoking inbox access                  |
|-----------------------------------|------------|----------------------------------------|

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import os
import logging
import asyncio
from pathlib import Path
from functools import wraps
from base64 import b64decode

from aiohttp import web
import jinja2
import aiohttp_jinja2

from .conf import CONF
from .utils import db

LOG = logging.getLogger('frontend')

def only_central_ega(async_func):
    '''Decorator restrain endpoint access to only Central EGA

       We use Basic Authentication.
       HTTPS will add security.
    '''
    @wraps(async_func)
    async def wrapper(request):
        auth_header = request.headers.get('AUTHORIZATION')
        if not auth_header:
            LOG.error('No header, No answer')
            raise web.HTTPUnauthorized(text=f'Protected access\n')
        _, token = auth_header.split(None, 1) # Skipping the Basic keyword
        cega_password = CONF.get('frontend','cega_password')
        request_user,request_password = b64decode(token).decode().split(':', 1)
        if request_user != "cega" or cega_password != request_password:
            LOG.error(f'CEGA password: {cega_password}')
            LOG.error(f'Request user: {request_user}')
            LOG.error(f'Request password: {request_password}')
            raise web.HTTPUnauthorized(text='Not authorized. You should be Central EGA.\n')
        # Otherwise, it is from CentralEGA, we continue
        res = async_func(request)
        res.__name__ = getattr(async_func, '__name__', None)
        res.__qualname__ = getattr(async_func, '__qualname__', None)
        return (await res)
    return wrapper

@aiohttp_jinja2.template('index.html')
async def index(request):
    '''Main endpoint with documentation

    The template is `index.html` in the configured template folder.
    '''
    return { 'country': 'Sweden', 'text' : '<p>There should be some info here.</p>' }

@only_central_ega
async def flush_user(request):
    '''Flush an EGA user from the database'''
    name = request.match_info['name']
    LOG.info(f'Flushing user {name} from the database')
    res = await db.flush_user(request.app['db'], name)
    if not res:
        raise web.HTTPBadRequest(text=f'An error occured for user {name}\n')
    return web.Response(text=f'Success')

@only_central_ega
async def status_file(request):
    '''Status endpoint for a given file'''
    filename = request.query['name']
    username = request.query['user']
    if not filename or not username:
        raise web.HTTPBadRequest(text=f'Invalid query\n')
    LOG.info(f'Getting info for file {filename} of user {username}')
    json_data = await db.get_file_info(request.app['db'], filename, username)
    if not json_data:
        raise web.HTTPNotFound(text=f'No info about file {filename} (from {username})\n')
    return web.json_response(json_data)

@only_central_ega
async def status_user(request):
    '''Status endpoint for a given file'''
    name = request.match_info['name']
    LOG.info(f'Getting info for user: {name}')
    json_data = await db.get_user_info(request.app['db'], name)
    if not json_data:
        raise web.HTTPBadRequest(text=f'No info for that user {name}... yet\n')
    return web.json_response(json_data)

async def init(app):
    '''Initialization running before the loop.run_forever'''
    app['db'] = await db.create_pool(loop=app.loop)
    LOG.info('DB Connection pool created')
    # Note: will exit on failure

async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')
    app['db'].close()
    await app['db'].wait_closed()

async def cleanup(app):
    '''Function run after a KeyboardInterrupt. Right after, the loop is closed'''
    LOG.info('Cancelling all pending tasks')
    for task in asyncio.Task.all_tasks():
        task.cancel()

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    loop = asyncio.get_event_loop()
    server = web.Application(loop=loop)

    # Where the templates are

    template_folder = CONF.get('frontend','templates',fallback=None) # lazy fallback
    if not template_folder:
        template_folder = Path(__file__).parent / 'conf' / 'templates'
    LOG.debug(f'Template folder: {template_folder}')
    template_loader = jinja2.FileSystemLoader(str(template_folder)) # let it crash if folder non existing
    aiohttp_jinja2.setup(server, loader=template_loader)

    # Registering the routes
    LOG.info('Registering routes')
    server.router.add_get( '/'              , index        , name='root'         )
    server.router.add_get( '/file'          , status_file  , name='status_file'  )
    server.router.add_get( '/user/{name}'   , status_user  , name='status_user'  )
    server.router.add_delete( '/user/{name}', flush_user   , name='flush_user'   )

    # Registering some initialization and cleanup routines
    LOG.info('Setting up callbacks')
    server.on_startup.append(init)
    server.on_shutdown.append(shutdown)
    server.on_cleanup.append(cleanup)

    # And ...... cue music!
    host=CONF.get('frontend','host')
    port=CONF.getint('frontend','port')
    LOG.info(f'Starting the real deal on <{host}:{port}>')
    web.run_app(server, host=host, port=port, shutdown_timeout=0)
    # https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web.py
    # run_app already catches the KeyboardInterrupt and calls loop.close() at the end

    LOG.info('Exiting the frontend')


if __name__ == '__main__':
    main()
