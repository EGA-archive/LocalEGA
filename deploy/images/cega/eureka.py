#!/usr/bin/env python3

'''\
A fake Eureka server.

Spinning the whole Spring Framework Netflix Eureka would take too long,
thus we are going to fake the responses.
'''

import sys
import asyncio
from aiohttp import web

import logging as LOG


routes = web.RouteTableDef()

# Followjng the responses from https://github.com/Netflix/eureka/wiki/Eureka-REST-operations


@routes.post('/eureka/apps/{app_name}')
async def register(request):
    """No matter the app it should register with success response 204."""
    return web.HTTPNoContent()

@routes.delete('/eureka/apps/{app_name}/{instance_id}')
async def deregister(request):
    """No matter the app it should deregister with success response 200."""
    return web.HTTPOk()

@routes.put('/eureka/apps/{app_name}/{instance_id}')
async def heartbeat(request):
    """No matter the app it should renew lease with success response 200."""
    return web.HTTPOk()

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

    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = 8761
    sslcontext = None

    loop = asyncio.get_event_loop()
    eureka = web.Application(loop=loop)
    eureka.router.add_routes(routes)

    # Registering some initialization and cleanup routines
    LOG.info('Setting up callbacks')
    eureka.on_startup.append(init)
    eureka.on_shutdown.append(shutdown)
    eureka.on_cleanup.append(cleanup)

    LOG.info(f"Start fake eureka on {host}:{port}")
    web.run_app(eureka, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
