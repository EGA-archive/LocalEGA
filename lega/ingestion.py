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

from aiohttp import web
from colorama import Fore
from aiopg.sa import create_engine

from .conf import CONF
from . import utils
from . import checksum
from . import amqp as broker
#from lega.db import Database

LOG = logging.getLogger(__name__)

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


async def process_file(n, submission_file, inbox, staging_area, staging_area_enc, msg):
    filename  = submission_file['filename']
    filehash  = submission_file['encryptedIntegrity']['hash']
    hash_algo = submission_file['encryptedIntegrity']['algorithm']

    inbox_filepath = os.path.join( inbox , filename )
    staging_filepath = os.path.join( staging_area , filename )
    staging_encfilepath = os.path.join( staging_area_enc , filename )

    ################# Check integrity of encrypted file
    LOG.debug(f'Verifying the {hash_algo} checksum of encrypted file: {inbox_filepath}')
    async with open(inbox_filepath, 'rb') as inbox_file: # Open the file in binary mode. No encoding dance.
        if not checksum.verify(inbox_file, filehash, hashAlgo = hash_algo):
            errmsg = f'Invalid {hash_algo} checksum for {inbox_filepath}'
            LOG.warning(errmsg)
            raise Exception(errmsg)
    LOG.debug(f'Valid {hash_algo} checksum for {inbox_filepath}')

    ################# Moving encrypted file to staging area
    await utils.mv( inbox_filepath, staging_filepath )
    LOG.debug(f'File moved:\n\tfrom {inbox_filepath}\n\tto {staging_filepath}')

    ################# Publish internal message for the workers
    # reusing same msg
    msg['filepath'] = staging_filepath
    msg['target'] = staging_encfilepath
    msg['hash'] = submission_file['unencryptedIntegrity']['hash']
    msg['hash_algo'] = submission_file['unencryptedIntegrity']['algorithm']
    await broker.publish(json.dumps(msg), routing_to=CONF.get('message.broker','routing_todo'))
    LOG.debug('Message sent to broker')

async def ingest(request):
    #assert( request[method == 'POST' )

    data = utils.get_data(await request.read())

    if not data:
        return "Error: Provide a base64-encoded message"

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

    loop = request.app.loop

    total = len(data['files'])
    width = len(str(total))
    success = 0
    n = 0

    for submission_file in data['files']:

        n +=1
        progress = f'[{n:{width}}/{total:{width}}] Ingesting {submission_file["filename"]}'
        LOG.info(f'{progress}\n')

        try:

            LOG.debug(f"Creating task for {submission_file['filename']}")
            #await loop.create_task(process_file, n, submission_file, inbox, staging_area, staging_area_enc, msg )
            await asyncio.sleep(2)

            success += 1
            response = f'{progress} {Fore.GREEN}✓{Fore.RESET}\n'
        except Exception as e:
            LOG.debug(repr(e))
            response = f'{progress} {Fore.RED}x{Fore.RESET}\n'

    return web.Response(text=response + f'Ingested {success} files (out of {total} files)\n')

async def shutdown(app):
    app['db'].close()
    await app['db'].wait_closed()

def main(args=None):

    if not args:
        args = sys.argv[1:]

    if '--conf' not in args:
        conf_file = os.environ.get('LEGA_CONF', None)
        if conf_file:
            print(f'USING {conf_file} as configuration file')
            args.append('--conf')
            args.append(conf_file)

    # re-conf
    CONF.setup(args)
    CONF.log_setup(LOG,'ingestion')
    # broker.setup()
    # CONF.log_setup(broker.LOG,'message.broker')

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


