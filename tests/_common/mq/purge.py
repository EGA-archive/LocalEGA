#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''Consumes messages from the specified broker. Effectively reseting the queues.'''

import argparse
import os
import ssl
import sys
from pathlib import Path

import pika

hellgate_queues = [ 'v1.files',
                    'v1.files.completed',
                    'v1.files.error',
                    'v1.files.inbox',
                    'v1.files.processing',
                    'v1.stableIDs',
]

parser = argparse.ArgumentParser(description=__doc__)

parser.add_argument('--connection',
                    help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'")

parser.add_argument('--queues', 
                    help='Comma-separated list of queues to consume from',
                    default=','.join(hellgate_queues))

args = parser.parse_args()


mq_connection = args.connection if args.connection else os.getenv('CEGA_CONNECTION',
                                                                  default="amqps://legatest:legatest@localhost:5670/%2F")
parameters = pika.URLParameters(mq_connection)

if mq_connection.startswith('amqps'):
    
    context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)  # Enforcing (highest) TLS version (so... 1.2?)

    context.check_hostname = False

    cacertfile = Path(__file__).parent / 'root.ca.crt'
    certfile = Path(__file__).parent / 'tester.ca.crt'
    keyfile = Path(__file__).parent / 'tester.ca.key'

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

for queue in args.queues.split(','):
    channel.queue_purge(queue=queue)
    print('Clean slate for',queue)

connection.close()
