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

from lega.conf import CONF
from lega import utils
from lega import checksum
from lega import amqp as broker
#from lega.db import Database

APP = Flask(__name__)
#LOG = APP.logger
LOG = logging.getLogger(__name__)

conf_file = os.environ.get('LEGA_CONF', None)
if conf_file:
    print('USING {} as configuration file'.format(conf_file))
    conf_file = ['--conf', conf_file]

CONF.setup(conf_file)
print(CONF)
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
    LOG.debug("Inbox area: {}".format(inbox))

    staging_area = utils.create_staging_area(submission_id)
    LOG.debug("Creating staging area: {}".format(staging_area))

    def process_files():
        for submission_file in data['files']:
            enchash       = submission_file['encryptedHash']
            hash_algo     = submission_file['hashAlgorithm']
            filename      = submission_file['filename']

            LOG.debug('* Ingesting {}'.format(filename))
            yield '* Ingesting {}\n'.format(filename)

            filepath = os.path.join( inbox , filename )
            ################# Check integrity of encrypted file
            LOG.debug('Verifying the {} checksum of encrypted file: {}'.format(hash_algo, filepath))

            with open(filepath, 'rb') as file_h: # Open the file in binary mode. No encoding dance.
                if not checksum.verify(file_h, enchash, hashAlgo = hash_algo):
                    errmsg = 'Invalid {} checksum for {}'.format(hash_algo, filepath)
                    LOG.debug(errmsg)
                    raise Exception(errmsg)

            LOG.debug('Valid {} checksum for {}'.format(hash_algo, filepath))

            ################# Moving encrypted file to staging area
            utils.mv( filepath, os.path.join( staging_area , filename ))

            ################# Publish internal message for the workers
            staging_area_enc = utils.create_staging_area(submission_id, group='enc')
            msg = {
                'filepath' : os.path.join( staging_area , filename ),
                'target'   : os.path.join( staging_area_enc , filename ),
                'hash'     : submission_file['unencryptedHash'],
                'hash_algo': hash_algo,
                'submission_id': submission_id,
                'user_id': user,
            }
            broker.publish(json.dumps(msg),
                           to_queue = CONF.get('worker','todo_queue'),
                           reply_queue = CONF.get('worker','success_queue'))
            LOG.debug('Message sent to broker')
        yield 'Ingested {} files\n'.format(len(data['files']))

    return Response(process_files(), mimetype='text/plain')
    #return

@APP.route('/ingest.fake', methods = ['GET'])
def ingest_fake():
    request.data = utils.fake_data()
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
