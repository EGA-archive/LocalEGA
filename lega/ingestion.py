#!/usr/bin/env python
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

from flask import Flask, request, g, Response

from .conf import CONF
from . import utils
from . import checksum
from . import amqp as broker
#from lega.db import Database

from colorama import Fore


APP = Flask(__name__)
#LOG = APP.logger
LOG = logging.getLogger(__name__)

conf_file = os.environ.get('LEGA_CONF', None)
if conf_file:
    print('USING {} as configuration file'.format(conf_file))
    conf_file = ['--conf', conf_file]

CONF.setup(conf_file)
CONF.log_setup(LOG,'ingestion')
broker.setup()
CONF.log_setup(broker.LOG,'message.broker')

@APP.route('/')
def index():
    return 'GOOOoooooodddd morning, Vietnaaaam!'

@APP.route('/ingest', methods = ['POST'])
def ingest():
    #assert( request.method == 'POST' )

    data = utils.get_data(request.data)

    if not data:
        return "Error: Provide a base64-encoded message"

    submission_id = data['submissionId']
    user          = data['user']

    inbox = utils.get_inbox(user)
    LOG.info(f"Inbox area: {inbox}")

    staging_area = utils.create_staging_area(submission_id)
    LOG.info(f"Staging area: {staging_area}")

    staging_area_enc = utils.create_staging_area(submission_id, group='enc')
    LOG.info(f"Staging area (for encryption): {staging_area_enc}")

    msg = {
        'filepath' : None,
        'target'   : None,
        'hash'     : None,
        'hash_algo': None,
        'submission_id': submission_id,
        'user_id': user,
    }

    def process_files(files, start=0):
        total = len(files)
        width = len(str(total))
        n = success = start
        for submission_file in files:
            try:
                n +=1
                filename      = submission_file['filename']
                enchash       = submission_file['encryptedHash']
                hash_algo     = submission_file['hashAlgorithm']

                LOG.info(f'[{n:{width}}/{total:{width}}] Ingesting {filename}')
                yield f'[{n:{width}}/{total:{width}}] Ingesting {filename}'

                ################# Check integrity of encrypted file
                filepath = os.path.join( inbox , filename )
                LOG.debug(f'Verifying the {hash_algo} checksum of encrypted file: {filepath}')
                with open(filepath, 'rb') as file_h: # Open the file in binary mode. No encoding dance.
                    if not checksum.verify(file_h, enchash, hashAlgo = hash_algo):
                        errmsg = f'Invalid {hash_algo} checksum for {filepath}'
                        raise Exception(errmsg)
                LOG.debug(f'Valid {hash_algo} checksum for {filepath}')

                ################# Moving encrypted file to staging area
                utils.mv( filepath, os.path.join( staging_area , filename ))

                ################# Publish internal message for the workers
                # reusing same msg
                msg['filepath'] = os.path.join( staging_area , filename )
                msg['target'] = os.path.join( staging_area_enc , filename )
                msg['hash'] = submission_file['unencryptedHash']
                msg['hash_algo'] = hash_algo
                broker.publish(json.dumps(msg), routing_to=CONF.get('message.broker','routing_todo'))
                LOG.debug('Message sent to broker')
                success += 1
                yield f' {Fore.GREEN}✓{Fore.RESET}\n'
            except Exception as e:
                LOG.debug(repr(e))
                yield f' {Fore.RED}x{Fore.RESET}\n'

        yield f'Ingested {success} files (out of {total} files)\n'

    return Response(process_files(data['files']), mimetype='text/plain')
    #return

@APP.route('/ingest.fake', methods = ['GET'])
def ingest_fake():
    request.data = utils.fake_data()
    return ingest()

@APP.route('/ingest.fake.small', methods = ['GET'])
def ingest_fake_small():
    request.data = utils.small_fake_data()
    return ingest()




# def get_db():
#     _db = getattr(g, '_db', None)
#     if _db is None:
#         _db = g._db = Database()
#         _db.setup()
#     return _db

# @APP.teardown_appcontext
# def close_connection(exception):
#     get_db().close()


# @APP.route('/status')
# def display():
#     return get_db().display()


# @APP.route('/status/<int:file_id>')
# def status(file_id):
#     return get_db().entry(file_id)


def main(args=None):

    if not args:
        args = sys.argv[1:]

    # re-conf
    CONF.setup(args)
    CONF.log_setup(LOG,'ingestion')
    broker.setup()
    CONF.log_setup(broker.LOG,'message.broker')

    APP.run(host=CONF.get('uwsgi','host'),
            port=CONF.getint('uwsgi','port'),
            debug=CONF.get('uwsgi','debug', fallback=False))

    return 0

if __name__ == '__main__':
    sys.exit( main() )
