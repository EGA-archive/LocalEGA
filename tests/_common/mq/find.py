#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads all messages from a queue and dumps the one with given
correlation id to stdout, if found"""

import sys
import json
import argparse
import os
import ssl
import sys
from pathlib import Path

import pika

# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--connection', help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'")
parser.add_argument('queue', help='The queue to listen to')
parser.add_argument('correlation_id', help="Fetch a given correlation id")
args = parser.parse_args()

# MQ Connection
mq_connection = args.connection if args.connection else os.getenv('CEGA_CONNECTION',
                                                                  default="amqps://legatest:legatest@localhost:5670/%2F")
parameters = pika.URLParameters(mq_connection)

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

messages = {}

# First loop, fetch all messages. Yeah, all in memory :(
while True:
    method_frame, props, body = channel.basic_get(queue=args.queue)

    if method_frame is None or props is None:
        break

    correlation_id = props.correlation_id
    message_id = method_frame.delivery_tag
    try:
        data = json.loads(body)
    except:
        data = {'non-json message' : body.decode()}

    message = '\t'.join(f'{k}: {v}' for k,v in data.items())

    if correlation_id in messages:  # we looped
        break
    messages[correlation_id] = (message_id, message)


# Second loop, nack the messages
for correlation_id, (message_id, message) in messages.items():
    channel.basic_nack(delivery_tag=message_id)

connection.close()

res = messages.get(args.correlation_id)

if res is None:
    sys.exit(2)

message_id, message = res
print( f'Message id: {message_id} | {message}' )
