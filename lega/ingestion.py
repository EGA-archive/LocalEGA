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

LOG = logging.getLogger('ingestion')

async def index(request):
    return web.Response(text='GOOOoooooodddd morning, Vietnaaaam!')

async def create_inbox(request):
    raise web.HTTPBadRequest(text='Not implemented yet!')

def process_submission(submission):
    '''Main function to process a submission.

    The argument is a dictionnary with information regarding one file submission.
    This function will be called upon request, and run in a separate process (a member of the ProcessPoolExecutor)
    '''

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


async def ingest(request):
    '''Ingestion endpoint

    When a request is received, the POST data is parsed by `utils.get_data`,
    and provides information about the list of files to ingest

    The data is of the form:
    * submission id
    * user


    We use a StreamResponse to send the response about each
    '''
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

    # Creating a listing of the tasks to run.
    success = 0
    total = len(data['files'])
    width = len(str(total))
    tasks = {} # (task -> str) mapping
    done = asyncio.Queue()

    for submission in data['files']:

        submission.update(submission_extra)

        task = asyncio.ensure_future(
            loop.run_in_executor(None, process_submission, submission) # default executor, set to ProcessPoolExecutor in main()
        ) # That will start running the task

        task.add_done_callback(lambda f: done.put_nowait(f))
        tasks[task] = submission['filename']

    # Running the tasks and getting the results as they arrive.
    for n in range(1,total+1):

        task = await done.get()
        filename = tasks[task]
        try:
            task.result() # May raise the exception caught in the separate process
            res = f'[{n:{width}}/{total:{width}}] {filename} {Fore.GREEN}✓{Fore.RESET}\n'
            success += 1 # no race here
        except Exception as e:
            LOG.error(f'Offloaded task came back with Error: {e!r}')
            res = f'[{n:{width}}/{total:{width}}] {filename} {Fore.RED}x{Fore.RESET}\n'

        # Send the result to the responde as they arrive
        await response.write(res.encode())
        await response.drain()

    assert( done.empty() )

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
    print('Shutting down...')
    app['db'].close()
    await app['db'].wait_closed()
    for task in asyncio.Task.all_tasks():
        task.cancel()
    app.loop.stop()

def main(args=None):

    if not args:
        import sys
        args = sys.argv[1:]

    if '--conf' not in args:
        conf_file = os.environ.get('LEGA_CONF')
        if conf_file:
            print(f'USING {conf_file} as configuration file')
            args.append('--conf')
            args.append(conf_file)

    CONF.setup(args) # re-conf

    loop = asyncio.get_event_loop()
    server = web.Application(loop=loop)
    executor = ProcessPoolExecutor(max_workers=None) # max_workers=None number of processors on the machine
    loop.set_default_executor(executor)

    # Registering the routes
    server.router.add_get('/', index)
    server.router.add_post('/ingest', ingest)
    server.router.add_get('/create-inbox', create_inbox)

    # Registering some initialization and cleanup routines
    server.on_startup.append(init)
    server.on_shutdown.append(shutdown)
    #server.on_cleanup.append(cleanup)

    # Registering when we close. Like catching the KeyboardInterrupt exception but better.
    # loop.add_signal_handler(signal.SIGINT,
    #                         functools.partial(executor.shutdown, wait=False)
    # )

    # And ...... cue music!
    web.run_app(server,
                host=CONF.get('ingestion','host'),
                port=CONF.getint('ingestion','port'),
                shutdown_timeout=0,
    )
    # https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web.py
    # run_app already catches the KeyboardInterrupt and calls loop.close() at the end

if __name__ == '__main__':
    main()


