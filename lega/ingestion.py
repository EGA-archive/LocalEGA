#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Re-Encryption Service
#
####################################
'''

__version__ = 0.1

import json
import os
import logging
import sys
import asyncio
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import signal
import functools
from random import randint

from aiohttp import web
from colorama import Fore
from aiopg.sa import create_engine

from .conf import CONF
from . import utils
from . import checksum
from . import amqp as broker
#from lega.db import Database

LOG = logging.getLogger(__name__)

# #_SIGMAP = dict((k, v) for v, k in signal.__dict__.items() if v.startswith('SIG'))
# def _default_handler(sig, frame):
#     this = multiprocessing.current_process()
#     print("{this!r} interrupted by a {sig} signal; exiting cleanly now", file=sys.stderr)
#     sys.exit(sig)


async def index(request):
    return web.Response(text='GOOOoooooodddd morning, Vietnaaaam!')


def register_sig_handler(signals=[signal.SIGINT, signal.SIGTERM],
                         handler=None):
    if handler is None:
        handler = _default_handler
    for sig in signals:
        signal.signal(sig, handler)


def process_submission(submission):

    inbox            = submission['inbox']
    staging_area     = submission['staging_area']
    staging_area_enc = submission['staging_area_enc']
    submission_id    = submission['submission_id']
    user_id          = submission['user_id']

    filename         = submission['filename']
    filehash         = submission['encryptedIntegrity']['hash']
    hash_algo        = submission['encryptedIntegrity']['algorithm']

    inbox_filepath = inbox / filename
    staging_filepath = staging_area / filename
    staging_encfilepath = staging_area_enc / filename

    ################# Check integrity of encrypted file
    LOG.debug(f'Verifying the {hash_algo} checksum of encrypted file: {inbox_filepath}')
    with open(inbox_filepath, 'rb') as inbox_file: # Open the file in binary mode. No encoding dance.
        if not checksum.verify(inbox_file, filehash, hashAlgo = hash_algo):
            errmsg = f'Invalid {hash_algo} checksum for {inbox_filepath}'
            LOG.warning(errmsg)
            raise Exception(errmsg)
    LOG.debug(f'Valid {hash_algo} checksum for {inbox_filepath}')

    ################# Moving encrypted file to staging area
    utils.mv( inbox_filepath, staging_filepath )
    LOG.debug(f'File moved:\n\tfrom {inbox_filepath}\n\tto {staging_filepath}')

    ################# Publish internal message for the workers
    # In the separate process
    msg = {
        'submission_id': submission_id,
        'user_id': user_id,
        'filepath': str(staging_filepath),
        'target' : str(staging_encfilepath),
        'hash': submission_file['unencryptedIntegrity']['hash'],
        'hash_algo': submission_file['unencryptedIntegrity']['algorithm'],
    }
    _,channel = broker.get_connection()
    broker.publish(channel, json.dumps(msg), routing_to=CONF.get('message.broker','routing_todo'))
    LOG.debug('Message sent to broker')

async def do_something():
    print('Johan is the King')
    await asyncio.sleep(1)
    #raise ValueError('42')
    print('Johan is the King 2')
    return 'Tja'

async def process_delay(func,*args):
    await asyncio.sleep(randint(1,5))
    await loop.run_in_executor(None, func, args)


async def ingest(request):
    #assert( request[method == 'POST' )

    data = utils.get_data(await request.read())


    if not data:
        raise web.HTTPBadRequest()
        #return web.Response(text='"Error: Empty POST data"', status=403)

    response = web.StreamResponse(status=200,
                                  reason='OK',
                                  headers={'Content-Type': 'text/html'})
    await response.prepare(request)

    response.write(b'Preparing for Ingestion\n')
    await response.drain()

    submission_id = data['submissionId']
    user_id       = data['userId']

    inbox = utils.get_inbox(user_id)
    LOG.info(f"Inbox area: {inbox}")

    staging_area = utils.staging_area(submission_id, create=True)
    LOG.info(f"Staging area: {staging_area}")

    staging_area_enc = utils.staging_area(submission_id, create=True, afterEncryption=True)
    LOG.info(f"Staging area (for encryption): {staging_area_enc}")

    loop = request.app.loop
    submission_extra = { 'inbox': inbox,
                         'staging_area': staging_area,
                         'staging_area_enc': staging_area_enc,
                         'submission_id': submission_id,
                         'user_id': user_id,
    }

    success = 0
    total = len(data['files'])
    width = len(str(total))
    tasks = {} # task -> name. Task is hashable
    for submission in data['files']:
        submission.update(submission_extra)

        #task = loop.run_in_executor(None, process_submission, submission) # default executor, set to ProcessPoolExecutor in main()
        task = process_delay(process_submission, submission)
        tasks[task] = submission["filename"]

    # await asyncio.wait(tasks.keys(), loop=request.app.loop, return_when=asyncio.ALL_COMPLETED)

    for n,result in enumerate(asyncio.as_completed(tasks.keys())):
        n += 1
        #title = tasks[result]

        try:
            await result # May raise the exception caught in the separate process
            #res = f'[{n:{width}}/{total:{width}}] {title} {Fore.GREEN}✓{Fore.RESET}\n'
            res = f'[{n:{width}}/{total:{width}}] {Fore.GREEN}✓{Fore.RESET}\n'
            success += 1 # no race here
        except Exception as e:
            LOG.error(repr(e))
            #res = f'[{n:{width}}/{total:{width}}] {title} {Fore.RED}x{Fore.RESET}\n'
            res = f'[{n:{width}}/{total:{width}}] {Fore.RED}x{Fore.RESET}\n'

        await response.write(res.encode())
        await response.drain()

    r = f'\nIngested {success} files (out of {total} files)\n'
    await response.write(r.encode())
    await response.write_eof()
    return response

async def init(app):
    app['db'] = await create_engine(user=CONF.get('db','username'),
                                    password=CONF.get('db','password'),
                                    host=CONF.get('db','host'),
                                    port=CONF.getint('db','port'),
                                    loop=app.loop) #database=CONF.get('db','uri'),

async def shutdown(app):
    app['db'].close()
    await app['db'].wait_closed()

def main(args=None):

    if not args:
        args = sys.argv[1:]

    if '--conf' not in args:
        conf_file = os.environ.get('LEGA_CONF')
        if conf_file:
            print(f'USING {conf_file} as configuration file')
            args.append('--conf')
            args.append(conf_file)

    # re-conf
    CONF.setup(args)
    CONF.log_setup(LOG,'ingestion')

    # Broker setup
    # global BROKER_CONNECTION, BROKER_CHANNEL
    # BROKER_CONNECTION, BROKER_CHANNEL = broker.get_connection()
    CONF.log_setup(broker.LOG,'message.broker')

    loop = asyncio.get_event_loop()

    EXECUTOR = ProcessPoolExecutor(max_workers=None) # max_workers=None number of processors on the machine
    loop.set_default_executor(EXECUTOR)

    server = web.Application(loop=loop)
    server.router.add_get('/', index)
    server.router.add_post('/ingest', ingest)
    server.on_startup.append(init)
    server.on_cleanup.append(shutdown)
    #server.on_shutdown.append(shutdown)

    try:
        web.run_app(server,
                    host=CONF.get('ingestion','host'),
                    port=CONF.getint('ingestion','port')
        )
    except KeyboardInterrupt:
        loop.stop()
    finally:
        EXECUTOR.shutdown(wait=True)
        EXECUTOR=None
        loop.close()

if __name__ == '__main__':
    main()


