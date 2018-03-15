#!/usr/bin/env python3

'''\
A fake Eureka server, because ..... Spaaaarta !
'''

import sys
import asyncio
from aiohttp import web
import logging

from .conf import CONF, KeysConfiguration

LOG = logging.getLogger('keyserver')
routes = web.RouteTableDef()

@routes.get('/hello')
async def hello(request):
    """Translate a file_id to a file_path"""
    return web.Response(text="Hi Stefan")


async def init(app):
    '''Initialization running before the loop.run_forever'''
    LOG.info('Initializing')

async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')

async def cleanup(app):
    '''Function run after a KeyboardInterrupt. Right after, the loop is closed'''
    LOG.info('Cancelling all pending tasks')

def main(args=None):
    """Where the magic happens."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)

    host = CONF.get('keyserver', 'host') # fallbacks are in defaults.ini
    port = CONF.getint('keyserver', 'port')
    keyserver_health = CONF.get('keyserver', 'health_endpoint')
    keyserver_status = CONF.get('keyserver', 'status_endpoint')

    eureka_endpoint = CONF.get('eureka', 'endpoint')

    sslcontext = None # Turning off SSL for the moment

    loop = asyncio.get_event_loop()
    keyserver = web.Application(loop=loop)
    keyserver.router.add_routes(routes)

    # Registering some initialization and cleanup routines
    LOG.info('Setting up callbacks')
    keyserver.on_startup.append(init)
    keyserver.on_shutdown.append(shutdown)
    keyserver.on_cleanup.append(cleanup)

    LOG.info(f"Start keyserver on {host}:{port}")
    web.run_app(keyserver, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)

if __name__ == '__main__':
    main()
