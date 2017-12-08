#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

'''Publishing a message, to a given message broker, for either the
creation of a user or the ingestion of a file.
'''

import argparse
import uuid
import json
import pika

parser = argparse.ArgumentParser(description='''Publish message to the broker on this machine.''')

parser.add_argument('--connection',
                    help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'",
                    default='amqp://localhost:5672/%2F')

parser.add_argument('routing', help='Routing key for the localega.v1 exchange')
parser.add_argument('user', help='Elixir ID')
parser.add_argument('filename', help='Filename in the user inbox')

unenc_group = parser.add_argument_group('unencrypted checksum')
unenc_group.add_argument('--unenc')
unenc_group.add_argument('--unenc_algo', default='md5', help='[Default: md5]')
enc_group = parser.add_argument_group('encrypted checksum')
enc_group.add_argument('--enc')
enc_group.add_argument('--enc_algo', default='md5', help='[Default: md5]')

args = parser.parse_args()

message = { 'elixir_id': args.user, 'filename': args.filename }
if args.enc:
    message['encrypted_integrity'] = { 'hash': args.enc, 'algorithm': args.enc_algo, }
if args.unenc:
    message['unencrypted_integrity'] = { 'hash': args.unenc, 'algorithm': args.unenc_algo, }

parameters = pika.URLParameters(args.connection)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.basic_publish(exchange='localega.v1', routing_key='{}.file'.format(args.routing),
                      body=json.dumps(message),
                      properties=pika.BasicProperties(correlation_id=str(uuid.uuid4()), content_type='application/json',delivery_mode=2))
connection.close()

