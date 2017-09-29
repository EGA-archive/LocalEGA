#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Publishing a message, to a given message broker, for either the
creation of a user or the ingestion of a file.
'''

import sys
import argparse
import uuid
import json
import pika
import logging

from ..conf import CONF
from .amqp import get_connection

LOG = logging.getLogger('publisher')

def make_file(args):
    msg = { 'elixir_id': args.user, 'filename': args.filename }
    if args.e:
        msg['encrypted_integrity'] = { 'hash': args.e, 'algorithm': args.ea, }
    if args.u:
        msg['unencrypted_integrity'] = { 'hash': args.u, 'algorithm': args.ua, }
    return msg

def main():
    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser(description='''Publish message to a given broker.''',
                                     allow_abbrev=False,
                                     epilog='The supported checksum algorithms are md5 and sha256')

    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')
    
    parser.add_argument('user', help='Elixir ID')
    parser.add_argument('filename', help='Filename in the user inbox')

    unenc_group = parser.add_argument_group('unencrypted checksum')
    unenc_group.add_argument('--unenc', dest='u')
    unenc_group.add_argument('--unenc_algo', dest='ua', default='md5', help='[Default: md5]')
    enc_group = parser.add_argument_group('encrypted checksum')
    enc_group.add_argument('--enc', dest='e')
    enc_group.add_argument('--enc_algo', dest='ea', default='md5', help='[Default: md5]')

    args = parser.parse_args()

    params = { 'correlation_id': str(uuid.uuid4()),
             'content_type' : 'application/json',
             'delivery_mode': 2, # make message persistent
    }

    message = make_file(args)

    connection = get_connection('cega.broker')
    channel = connection.channel()
    channel.basic_publish(exchange='localega.v1', routing_key='sweden.file',
                          body=json.dumps(message),
                          properties=pika.BasicProperties(**params))

    connection.close()


if __name__ == '__main__':
    main()
