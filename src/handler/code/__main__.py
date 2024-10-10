#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import asyncio

import asyncpg

from .utils import conf, amqp, exceptions
from .utils.json import FEGAMessage
from .handlers import (ingest,
                       cancel,
                       # heartbeat,
                       accession,
                       user,
                       dataset,
                       dac)

LOG = logging.getLogger(__name__)

def mq_report(func):
    async def wrapper(config, message):
        try:
            return await func(config, message)
        except exceptions.FromUser as e:
            LOG.error('Publish error to Central EGA: %r', e)
            # publish to Central EGA
            error = {
                'user': message.parsed.get('user','unknown'),
                'filepath': message.parsed.get('filepath', 'unknown'),
                'reason': repr(e),
            }
            if 'encrypted_checksums' in message.parsed:
                error['encrypted_checksums'] = message.parsed.get('encrypted_checksums')
            await config.mq.cega_publish(error, 'files.error', correlation_id=message.header.properties.content_type)
        except Exception as e: # any other error
            LOG.error('Publish error to Local EGA Sys admins: %r', e)
            error = {
                'error': repr(e),
                'message': message.content,
            }
            await config.mq.lega_publish(error, 'system.error', correlation_id=message.header.properties.content_type)
    return wrapper

def ack_nack_on_exception(on_message):
    async def wrapper(*args, **kwargs):
        message = args[-1]
        try:
            await on_message(*args, **kwargs)
            LOG.info('Acking message %d', message.delivery.delivery_tag)
            await message.channel.basic_ack(message.delivery.delivery_tag)
        except Exception as e:
            LOG.error('%r', e, exc_info=True)
            LOG.info('Nacking message %d', message.delivery.delivery_tag)
            await message.channel.basic_nack(message.delivery.delivery_tag, requeue=False)
            raise e
    return wrapper

@mq_report # report after we ack/nack
@ack_nack_on_exception
async def work(config, message):

    correlation_id = message.header.properties.correlation_id
    LOG.info('Working on message %d', message.delivery.delivery_tag, extra={'correlation_id': correlation_id})

    job_type = message.parsed.get('type', None)
    LOG.info('Job type: %s', job_type)
    if job_type is None:
        raise Exception('Missing job type: Invalid message')


    LOG.debug('Message: %s', message.parsed)

    if job_type == 'ingest':
        # delay in case another worker picked up a cancel message fast
        await asyncio.sleep(1)

        await ingest.execute(config, message)
    elif job_type == 'cancel':

        await cancel.execute(config, message)

    elif job_type == 'accession':
        await accession.execute(config, message)

    elif job_type == 'mapping':

        await dataset.execute(config, message)

    elif job_type == 'deprecate':

        await dataset.deprecate(config, message)

    elif job_type == 'release':

        await dataset.release(config, message)

    elif job_type == 'permission':

        await dataset.permission(config, message)

    elif job_type == 'permission.deleted':

        await dataset.delete_permission(config, message)

#    elif job_type == 'user':
#
#        await user.execute(config, message)

    elif job_type == 'password.updated':

        await user.password(config, message)

    elif job_type == 'contact.updated':

        await user.contact(config, message)

    elif job_type == 'keys.updated':

        await user.keys(config, message)

    elif job_type == 'dac.dataset':

        await dac.dataset(config, message)

    elif job_type == 'dac.members':

        await dac.members(config, message)

    elif job_type == 'dac':

        await dac.update(config, message)


    # elif job_type == 'heartbeat':
    #     await heartbeat.execute(config, data)

    # We need to send 2 heartbeats with an interval, and check that the FEGA node missed 2.
    # On CentralEGA side, we save the time of the heartbeats and clear the timeouts when a heartbeat answered.
    # That is re-inventing the wheel: we re-implement the heartbeat protocol built in AMQP itself.
    #
    # That said, if CentralEGA sends a heartbeat message and the FEGA node is not connected,
    # nor pulling the federated queue, the messages will stay there.
    #
    # If the messages are picked and we don’t get a completed, the jobs are not finished.
    # If the messages are not picked, the jobs are not finished either.
    # The messages are then staying in the queue: they don’t travel if no one is pulling on the other side.
    #
    # In conclusions, if we do need an implementation for a heartbeat feature,
    # we simply check if the message queue is emptying, and if we receive the completed messages.

    else:
        raise Exception(f'Invalid operation: {job_type} for message: {message.content}')




def capture_all_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            LOG.error('General error: %r', e, exc_info=True)
            sys.exit(2)
    return wrapper

@capture_all_errors
async def main(conf_file):

    os.umask(0o007) # no world permissions

    config = conf.Configuration(conf_file)
    LOG.debug('Config ready: %s', config)

    # pinging the DB first
    await config.db.ping()

    LOG.info('Setup completed')

    async def do_work(message):
        try:
            await work(config, FEGAMessage(message))
        except Exception as e:
            LOG.error('ERROR: %r', e, exc_info=True)

    LOG.info('Consuming')
    return await config.mq.consume(do_work)



if __name__ == '__main__':

    if len(sys.argv) < 2:
        command = ' '.join(sys.orig_argv)
        print(f'Usage: {command} <conf_file>')
        sys.exit(1)
    loop = asyncio.get_event_loop()
    loop.create_task(main(sys.argv[1]))
    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        LOG.warning('Cancelled')
        sys.exit(1)

