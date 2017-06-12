#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Ingestion API Front-end
#
####################################

We provide:

|---------------------------------------|-----------------|----------------|
| endpoint                              | accepted method |     Note       |
|---------------------------------------|-----------------|----------------|
| [LocalEGA-URL]/                       |       GET       |                |
| [LocalEGA-URL]/user/inbox             |       POST      | requires login |
| [LocalEGA-URL]/status/file/<id>       |       GET       |                |
| [LocalEGA-URL]/status/user/<id>       |       GET       |                |
|---------------------------------------|-----------------|----------------|

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import os
import logging
import asyncio
from pathlib import Path

from aiohttp import web
import jinja2
import aiohttp_jinja2

from .conf import CONF
from . import db
from .utils import only_central_ega

LOG = logging.getLogger('frontend')

@aiohttp_jinja2.template('index.html')
async def index(request):
    '''Main endpoint with documentation

    The template is `index.html` in the configured template folder.
    '''
    return { 'country': 'Sweden', 'text' : '<p>There should be some info here.</p>' }

@only_central_ega
async def status_file(request):
    '''Status endpoint for a given file'''
    file_id = request.match_info['id']
    LOG.info(f'Getting info for file_id {file_id}')
    res = await db.get_file_info(request.app['db'], file_id)
    if not res:
        raise web.HTTPBadRequest(text=f'No info about file with id {file_id}... yet\n')
    filename, status, created_at, last_modified, stable_id = res
    return web.Response(text=f'Status for {file_id}: {status}'
                        f'\n\t* Created at: {created_at}'
                        f'\n\t* Last updated: {last_modified}'
                        f'\n\t* Submitted file name: {filename}'
                        f'\n\t* Stable file name: {stable_id}\n')

@only_central_ega
async def status_user(request):
    '''Status endpoint for a given file'''
    user_id = request.match_info['id']
    LOG.info(f'Getting info for user: {user_id}')
    res = await db.get_user_info(request.app['db'], user_id)
    if not res:
        raise web.HTTPBadRequest(text=f'No info for that user {user_id}... yet\n')
    json_data = [ { 'filename': info[0],
                    'status': str(info[1]),
                    'created_at': str(info[2]),
                    'last_modifed': str(info[3]),
                    'final_name': info[4] } for info in res]
    return web.json_response(json_data)

async def _connect_db(app):
    try:
        app['db'] = await db.create_pool(loop=app.loop,
                                         user=CONF.get('db','username'),
                                         password=CONF.get('db','password'),
                                         database=CONF.get('db','dbname'),
                                         host=CONF.get('db','host'),
                                         port=CONF.getint('db','port'))

        LOG.info('DB Engine created')

    except Exception as e:
        print('Connection error to the Postgres database\n',str(e))
        app.loop.call_soon(app.loop.stop)
        app.loop.call_soon(app.loop.close)
        sys.exit(2)

async def init(app):
    '''Initialization running before the loop.run_forever'''
    await _connect_db(app)

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
        template_folder = Path(__file__).parent / 'templates'
    LOG.debug(f'Template folder: {template_folder}')
    template_loader = jinja2.FileSystemLoader(str(template_folder)) # let it crash if folder non existing
    aiohttp_jinja2.setup(server, loader=template_loader)

    # Registering the routes
    LOG.info('Registering routes')
    server.router.add_get( '/'                      , index        , name='root'             )
    server.router.add_get( '/status/file/{id}'      , status_file  , name='status_file'      )
    server.router.add_get( '/status/user/{id}'      , status_user  , name='status_user'      )

    # Registering some initialization and cleanup routines
    LOG.info('Setting up callbacks')
    server.on_startup.append(init)
    server.on_shutdown.append(shutdown)
    server.on_cleanup.append(cleanup)

    # And ...... cue music!
    LOG.info('Starting the real deal')
    web.run_app(server,
                host=CONF.get('frontend','host'),
                port=CONF.getint('frontend','port'),
                shutdown_timeout=0,
    )
    # https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web.py
    # run_app already catches the KeyboardInterrupt and calls loop.close() at the end

    LOG.info('Exiting the frontend')

if __name__ == '__main__':
    main()

