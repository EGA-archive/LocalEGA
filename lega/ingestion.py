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

from aiohttp import web
from colorama import Fore
from aiopg.sa import create_engine

from .conf import CONF
from . import utils
from . import checksum
from . import amqp as broker
#from lega.db import Database

LOG = logging.getLogger(__name__)
#EXECUTOR = ProcessPoolExecutor(max_workers=10) # None = Default one.  Otherwise ThreadPoolExecutor() or
EXECUTOR = ProcessPoolExecutor(max_workers=None) # max_workers=None number of processors on the machine

# #_SIGMAP = dict((k, v) for v, k in signal.__dict__.items() if v.startswith('SIG'))
# def _default_handler(sig, frame):
#     this = multiprocessing.current_process()
#     print("{this!r} interrupted by a {sig} signal; exiting cleanly now", file=sys.stderr)
#     sys.exit(sig)

async def init(app):
    engine = await create_engine(#database=CONF.get('db','uri'),
                                 user=CONF.get('db','username'),
                                 password=CONF.get('db','password'),
                                 host=CONF.get('db','host'),
                                 port=CONF.getint('db','port'),
                                 loop=app.loop)
    app['db'] = engine

async def index(request):
    return web.Response(text='GOOOoooooodddd morning, Vietnaaaam!')


def register_sig_handler(signals=[signal.SIGINT, signal.SIGTERM],
                         handler=None):
    if handler is None:
        handler = _default_handler
    for sig in signals:
        signal.signal(sig, handler)


def process_file(submission_file, inbox, staging_area, staging_area_enc, submission_id, user_id):

    try:
        filename  = submission_file['filename']
        filehash  = submission_file['encryptedIntegrity']['hash']
        hash_algo = submission_file['encryptedIntegrity']['algorithm']

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
        msg = {
            'submission_id': submission_id,
            'user_id': user_id,
            'filepath': str(staging_filepath),
            'target' : str(staging_encfilepath),
            'hash': submission_file['unencryptedIntegrity']['hash'],
            'hash_algo': submission_file['unencryptedIntegrity']['algorithm'],
        }
        broker.publish(json.dumps(msg), routing_to=CONF.get('message.broker','routing_todo'))
        LOG.debug('Message sent to broker')
        return (True, f'{Fore.GREEN}✓{Fore.RESET}')
    except Exception as e:
        LOG.error(repr(e))
        return (False, f'{Fore.RED}x{Fore.RESET}')

async def ingest(request):
    #assert( request[method == 'POST' )

    data = utils.get_data(await request.read())

    if not data:
        return web.Response(text='"Error: Provide a base64-encoded message"')

    submission_id = data['submissionId']
    user_id       = data['userId']

    inbox = utils.get_inbox(user_id)
    LOG.info(f"Inbox area: {inbox}")

    staging_area = utils.staging_area(submission_id, create=True)
    LOG.info(f"Staging area: {staging_area}")

    staging_area_enc = utils.staging_area(submission_id, create=True, afterEncryption=True)
    LOG.info(f"Staging area (for encryption): {staging_area_enc}")

    # Common attributes for message. Object will be reused
    msg = { 'submission_id': submission_id, 'user_id': user_id }

    total = len(data['files'])
    width = len(str(total))

    results = []
    success = 0
    tasks = {}
    loop = request.app.loop

    for n,submission_file in enumerate(data['files']):
        n += 1 # Not from 0
        progress = f'[{n:{width}}/{total:{width}}] Ingesting {submission_file["filename"]}'
        LOG.info(f'{progress}\n')

        job = functools.partial(process_file, submission_file, inbox, staging_area, staging_area_enc, submission_id, user_id)
        #task = asyncio.ensure_future(job(), loop=loop)
        #task = asyncio.run_coroutine_threadsafe(job(), loop=loop)
        task = loop.run_in_executor(EXECUTOR, job)
        assert progress not in tasks
        tasks[progress] = task

    await asyncio.wait(tasks.values(), loop=loop, return_when=asyncio.ALL_COMPLETED)
    #await asyncio.gather(tasks.values(), loop=loop, return_exceptions=False)


    await asyncio.sleep(10)

    for progress, task in tasks.items():
        r,rmsg = task.result()
        if r:
            success += 1  # no race here
        results.append(f'{progress} {rmsg}')

    return web.Response(
        text='\n'.join(results) + f'\nIngested {success} files (out of {total} files)\n'
    )

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
    broker.setup()
    CONF.log_setup(broker.LOG,'message.broker')

    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop)

    app.router.add_get('/', index)
    app.router.add_post('/ingest', ingest)

    app.on_startup.append(init)
    app.on_cleanup.append(shutdown)
    #app.on_shutdown.append(shutdown)

    web.run_app(app,
                host=CONF.get('ingestion','host'),
                port=CONF.getint('ingestion','port')
    )

if __name__ == '__main__':
    main()


