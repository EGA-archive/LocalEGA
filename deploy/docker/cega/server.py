import logging
import argparse
from pathlib import Path
from logging.config import dictConfig
import sys
import json
import asyncio
from base64 import b64decode

from aiohttp import web
import aiormq

LOG = logging.getLogger(__name__)

HTTP_AUTH_USERNAME = 'fega'
HTTP_AUTH_PASSWORD = 'testing' # yup, we don't care, it's just for testing

#############################################################
## Consumer 
#############################################################

async def on_message(message, publish_channel):
    try:
        correlation_id = message.header.properties.correlation_id
        body = message.body.decode()
        LOG.debug('[%s] %s', correlation_id, body)
        await message.channel.basic_ack(message.delivery.delivery_tag)
    except Exception as e:
        LOG.error('%r', e)
        await message.channel.basic_nack(message.delivery.delivery_tag)

#############################################################
## Central EGA users 
#############################################################
USERS = {}

async def get_user(request):

    # Authenticate
    auth_header = request.headers.get('AUTHORIZATION')
    if not auth_header:
        raise web.HTTPUnauthorized(reason='Protected access')
    _, token = auth_header.split(None, 1)  # Skipping the Basic keyword
    auth_user, auth_password = b64decode(token).decode().split(':', 1)
    if HTTP_AUTH_USERNAME != auth_user or HTTP_AUTH_PASSWORD != auth_password:
        raise web.HTTPUnauthorized(reason='Protected access')

    # Search
    term = request.match_info.get('term')
    record = USERS.get(term)

    if not record:
        raise web.HTTPNotFound(reason='User not found')

    return web.json_response(record,
                             headers = { "Server": "Central EGA (test) Server",
                                         "X-EGA-apiVersion" : "v2",
                                         "X-EGA-docLink" : "https://ega-archive.org",
                                        })

def load_users(filepath):
    global USERS
    with open(filepath, 'r') as stream:
        USERS = json.load(stream)
    LOG.debug('Loaded %d users: %s', len(USERS) / 2, list(USERS.keys()))


#############################################################
## Server init/destroy
#############################################################

async def initialize(app, mq_url, queue, prefetch=None):
    """Initialize server."""

    mq = await aiormq.connect(mq_url)
    app['mq'] = mq

    channel = await mq.channel()
    publish_channel = await mq.channel()
    if prefetch:
        prefetch = int(prefetch)
        LOG.debug('Prefetch: %s', prefetch)
        await channel.basic_qos(prefetch_count=prefetch)
    
    LOG.debug('Creating consumer for %s', queue)
    app['mq_consumer'] = None
    try:

        async def _on_message(message):
            return await on_message(message, publish_channel)

        task = asyncio.create_task(channel.basic_consume(queue, _on_message, no_ack=False, consumer_tag='LocalEGA-test'))
        app['mq_consumer'] = task
        def discard():
            app['mq_consumer'] = None
        task.add_done_callback(discard)
    except asyncio.CancelledError as e:
        LOG.error('Cancelled: %s', e)
        raise ValueError('MQ Consumer error')

    LOG.info("Initialization done.")

async def destroy(app):
    LOG.info("Shutting down.")
    task = app['mq_consumer']
    if task:
        task.cancel()
    await app['mq'].close()


#############################################################
## ....and cue music
#############################################################

@web.middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except web.HTTPException as e:
        # LOG.error('%r', e)
        raise e
    except Exception as e:
        LOG.error('%r', e, exc_info=True)
        raise e

def main(port, users_filepath, mq_url, queue, mq_prefetch=None):

    # Load Users
    load_users(users_filepath)

    # Configure the app
    server = web.Application(middlewares = [error_middleware])
    async def _init(app):
        await initialize(app, mq_url, queue, prefetch=mq_prefetch)
    server.on_startup.append(_init)
    server.on_cleanup.append(destroy)

    # Configure the endpoints
    server.add_routes([web.get('/username/{term}', get_user),
                       web.get('/user-id/{term}', get_user),
                       ])

    # run the server on a port number
    web.run_app(server,
                host='0.0.0.0',
                port=port,
                shutdown_timeout=0, ssl_context=None)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Fake Central EGA server/consumer')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-u', '--users', default=str(Path(__file__).parent.resolve() / 'users.json'))
    parser.add_argument('-q', '--queue', default='from_fega')
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-b', '--broker')
    parser.add_argument('-f', '--prefetch', type=int, default=None)
    

    args = parser.parse_args()

    log_level = 'CRITICAL'
    if args.verbose:
        log_level = 'INFO'
    if args.debug:
        log_level = 'DEBUG'

    print(args)

    # Configure the logging
    dictConfig({ "version": 1,
                 "root": {
                     "level": "NOTSET",
                     "handlers": [ "noHandler" ]
                 },
                 "loggers": {
                     "__main__": {
                         "level": log_level,
                         "propagate": True,
                         "handlers": [ "console" ]
                     },
                     "aiormq": {
                         "level": "CRITICAL",
                         "handlers": [ "console" ]
                     },
                     "aiohttp": {
                         "level": "CRITICAL",
                         "handlers": [ "console" ]
                     },
                     "asyncio": {
                         "level": "CRITICAL",
                         "handlers": [ "console" ]
                     }
                 },
                 "handlers": {
                     "noHandler": {
                         "class": "logging.NullHandler",
                         "level": "NOTSET"
                     },
                     "console": {
                         "class": "logging.StreamHandler",
                         "formatter": "simple",
                         "stream": "ext://sys.stderr"
                     }
                 },
                 "formatters": {
                     "simple": {
                         "format": "[{name:^10}][{levelname:^6}] (L{lineno}) {message}",
                         "style": "{"
                     }
                 }
                })

    main(args.port, args.users, args.broker, args.queue, mq_prefetch = args.prefetch)
