import logging
import argparse
from pathlib import Path
from logging.config import dictConfig
import asyncio

from aiohttp import web
import aiormq

from . import users, mq, request

LOG = logging.getLogger(__name__)

#############################################################
## Server init/destroy
#############################################################

async def initialize(app, users_filepath, mq_url, queue, prefetch=None):
    """Initialize server."""

    # Load users
    app['users'] = users.load_users(users_filepath)

    mq_connection = await aiormq.connect(mq_url)
    app['mq'] = mq_connection

    channel = await mq_connection.channel()
    publish_channel = await mq_connection.channel()
    app['mq_channel'] = publish_channel
    if prefetch:
        prefetch = int(prefetch)
        LOG.debug('Prefetch: %s', prefetch)
        await channel.basic_qos(prefetch_count=prefetch)
    
    LOG.debug('Creating consumer for %s', queue)
    app['mq_consumer'] = None
    try:

        async def _on_message(message):
            try:
                await mq.on_message(message, publish_channel)
                await message.channel.basic_ack(message.delivery.delivery_tag)
            except Exception as e:
                LOG.error('%r', e)
                await message.channel.basic_nack(message.delivery.delivery_tag)

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

    # Configure the app
    server = web.Application(middlewares = [error_middleware])
    async def _init(app):
        await initialize(app, users_filepath, mq_url, queue, prefetch=mq_prefetch)
    server.on_startup.append(_init)
    server.on_cleanup.append(destroy)

    # Configure the endpoints
    server.add_routes([web.get('/username/{term}', users.get_user),
                       web.get('/user-id/{term}', users.get_user),
                       web.get('/permission/{username}/{dataset_id}', request.grant_permission),
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
    parser.add_argument('-u', '--users', default=str(Path(__file__).parent.parent.resolve() / 'users.json'))
    parser.add_argument('-q', '--queue', default='from_fega')
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-f', '--prefetch', type=int, default=None)
    parser.add_argument('broker')
    
    args = parser.parse_args()

    log_level = 'CRITICAL'
    if args.verbose:
        log_level = 'INFO'
    if args.debug:
        log_level = 'DEBUG'

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
                     "server": {
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
