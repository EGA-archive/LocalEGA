#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''Publishing a message to CentralEGA, given a routing key.'''

import argparse
import uuid
import json
import string
import secrets
import os
import ssl
import sys
from pathlib import Path

import pika

parser = argparse.ArgumentParser(description='''Publish message to the broker on this machine.''')
parser.add_argument('--connection',
                    help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'")
parser.add_argument('--correlation_id', default=None)
parser.add_argument('routing_key', help='The routing key used for the CentralEGA exchange')
parser.add_argument('message', help='A JSON-formatted string')

args = parser.parse_args()

correlation_id = args.correlation_id if args.correlation_id else str(uuid.uuid4())

# Just checking the JSON-formatting
message = json.loads(args.message)

mq_connection = args.connection if args.connection else os.getenv('CEGA_CONNECTION',
                                                                  default="amqps://legatest:legatest@localhost:5670/%2F")
parameters = pika.connection.URLParameters(mq_connection)


if mq_connection.startswith('amqps'):

    context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)  # Enforcing (highest) TLS version (so... 1.2?)

    context.check_hostname = False

    cacertfile = Path(__file__).parent / 'CA.cert.pem'
    certfile = Path(__file__).parent / 'testsuite.cert.pem'
    keyfile = Path(__file__).parent / 'testsuite.sec.pem'

    context.verify_mode = ssl.CERT_NONE
    # Require server verification
    if cacertfile.exists():
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=str(cacertfile))
        
    # If client verification is required
    if certfile.exists():
        assert( keyfile.exists() )
        context.load_cert_chain(str(certfile), keyfile=str(keyfile))

    # Finally, the pika ssl options
    parameters.ssl_options = pika.SSLOptions(context=context, server_hostname=None)


connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.basic_publish(exchange='localega.v1', routing_key=args.routing_key,
                      body=json.dumps(message),
                      properties=pika.BasicProperties(correlation_id=correlation_id,
                                                      content_type='application/json',
                                                      delivery_mode=2))

connection.close()
print('Message published to CentralEGA')

