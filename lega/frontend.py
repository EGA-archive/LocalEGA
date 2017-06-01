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
import json
from pathlib import Path

from colorama import Fore, Back
from aiohttp import web
from aiohttp_swaggerify import swaggerify
import aiohttp_cors
import jinja2
import aiohttp_jinja2
import aioamqp

from .conf import CONF
from . import db
from .utils import only_central_ega, get_data

LOG = logging.getLogger('frontend')

@aiohttp_jinja2.template('index.html')
async def index(request):
    '''Main endpoint with documentation

    The template is `index.html` in the configured template folder.
    '''
    #return web.Response(text=f'\n{Fore.BLACK}{Back.YELLOW}GOOOoooooodddd morning, Vietnaaaam!{Back.RESET}{Fore.RESET}\n\n')
    return { 'country': 'Sweden', 'text' : '<p>There should be some info here.</p>' }
      
@only_central_ega
async def inbox(request):
    '''Inbox creation endpoint'''
    data = get_data(await request.text())
    if not data:
        raise web.HTTPBadRequest(text=f'\n{Fore.BLACK}{Back.RED}No data provided!{Back.RESET}{Fore.RESET}\n\n')

    elixir_id = data.get('elixir_id',None)
    password = data.get('password', None)
    pubkey = data.get('pubkey', None)
    assert elixir_id, "We need an elixir-id"
    assert (password or pubkey), "We need either a password or a public key"

    # No sanitizing here
    msg = { 'user_id' : elixir_id,
            'password': password,
            'pubkey' : pubkey,
    }

    # Check if valid user
    # TODO

    # Add to database
    await db.insert_user(request.app['db'], **msg)

    _, protocol = request.app['broker']
    channel = await protocol.channel()
    await channel.basic_publish(payload = json.dumps(msg),
                                exchange_name = CONF.get('local.broker','exchange'),
                                routing_key = CONF.get('local.broker','routing_user'))

    return web.Response(text=f'Message internally published\n')

@only_central_ega
async def outgest(request):
    '''Outgestion endpoint

    Not implemented yet.
    '''
    raise web.HTTPBadRequest(text=f'\n{Fore.BLACK}{Back.RED}Not implemented yet!{Back.RESET}{Fore.RESET}\n\n')

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
                        f'\n\t* Submitted file name: {filename}\n'
                        f'\n\t* Stable file name: {stable_id}\n')

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

async def _connect_mq(app):
    try:
        kwargs = { 'loop': app.loop }
        heartbeat = CONF.getint('localhost','heartbeat', fallback=None)
        if heartbeat is not None: # can be 0
            kwargs['heartbeat_interval'] = heartbeat
            LOG.info(f'Setting hearbeat to {heartbeat}')

        app['broker'] = await aioamqp.connect(host = CONF.get('local.broker','host',fallback='localhost'),
                                              port = CONF.getint('local.broker','port',fallback=5672),
                                              virtualhost = CONF.get('local.broker','vhost',fallback='/'),
                                              login = CONF.get('local.broker','username'),
                                              password = CONF.get('local.broker','password'),
                                              ssl = False,
                                              loop = app.loop,
                                              kwargs=kwargs)

        LOG.info('Local Message broker connected')
    except Exception as e:
        print('Connection error to the Message broker\n',str(e))
        app.loop.call_soon(app.loop.stop)
        app.loop.call_soon(app.loop.close)
        sys.exit(2)


async def init(app):
    '''Initialization running before the loop.run_forever'''
    await _connect_db(app)
    await _connect_mq(app)

async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')
    app['db'].close()
    await app['db'].wait_closed()

    transport,protocol = app['broker']
    await protocol.close()
    transport.close()

async def cleanup(app):
    '''Function run after a KeyboardInterrupt. Right after, the loop is closed'''
    LOG.info('Cancelling all pending tasks')
    for task in asyncio.Task.all_tasks():
        task.cancel()

# async def swagger_json(request):
#     return web.json_response(
#         request.app["_swagger_config"],
#         headers={ "X-Custom-Server-Header": "Custom data",})

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    loop = asyncio.get_event_loop()
    server = web.Application(loop=loop)

    # Where the templates are

    template_folder = CONF.get('ingestion','templates',fallback=None) # lazy fallback
    if not template_folder:
        template_folder = str(Path(__file__).parent / 'templates')
    LOG.debug(f'Template folder: {template_folder}')
    template_loader = jinja2.FileSystemLoader(template_folder)

    aiohttp_jinja2.setup(server, loader=template_loader)

    # Registering the routes
    LOG.info('Registering routes')
    server.router.add_get( '/'                      , index        , name='root'             )
    server.router.add_post('/user/inbox'            , inbox        , name='inbox'            )
    server.router.add_get( '/status/file/{id}'      , status_file  , name='status_file'      )
    server.router.add_get( '/status/user/{id}'      , status_user  , name='status_user'      )
    server.router.add_post('/outgest'               , outgest      , name='outgestion'       )

    # # Swagger endpoint: /swagger.json
    # LOG.info('Preparing for Swagger')
    # swaggerify(server)
    # cors = aiohttp_cors.setup(server) # Must enable CORS
    # for route in server.router.routes(): # I don't bother and enable CORS for all routes
    #     cors.add(route, {
    #         CONF.get('swagger','url') : aiohttp_cors.ResourceOptions(
    #             allow_credentials=True,
    #             expose_headers=("X-Custom-Server-Header",),
    #             allow_headers=("X-Requested-With", "Content-Type"),
    #             max_age=3600,
    #         )
    #     })

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

    # LOG.info('Shutting down the executor')
    # executor.shutdown(wait=True)
    # # Done on exit of the with statement
    # # https://github.com/python/cpython/blob/master/Lib/concurrent/futures/_base.py#L580-L582

    LOG.info('Exiting the Ingestion server')

if __name__ == '__main__':
    main()

