#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Consumes the first message from a queue, if the user+filepath match"""

import sys
import json
import argparse
import os
import ssl
import sys

import pika


# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--connection', help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'")
parser.add_argument('queue', help="Queue to read")
parser.add_argument('user')
parser.add_argument('filepaths', metavar='filepath', nargs='+')
args = parser.parse_args()

# MQ Connection
mq_connection = args.connection if args.connection else os.getenv('CEGA_CONNECTION',
                                                                  default="amqps://legatest:legatest@localhost:5670/%2F")
parameters = pika.URLParameters(mq_connection)

if mq_connection.startswith('amqps'):

    context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS) # Enforcing (highest) TLS version (so... 1.2?)

    # Ignore the server and client verification
    context.verify_mode = ssl.CERT_NONE
    context.check_hostname = False
    
    # Finally, the pika ssl options
    parameters.ssl_options = pika.SSLOptions(context=context, server_hostname=None)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

correlation_ids = []

messages = set()
consume_messages = set()
reject_messages = set()

filepaths = set()
for fp in args.filepaths:
    filepaths.add(fp)

# First loop, fetch all messages. Yeah, all in memory :(
while True:
    method_frame, props, body = channel.basic_get(queue=args.queue)

    if method_frame is None or props is None:
        break

    message_id = method_frame.delivery_tag
    if message_id in messages:  # we looped
        break
    messages.add(message_id)

    try:
        data = json.loads(body)
        user = data.get('user')
        filepath = data.get('filepath')
        assert( user and filepath ) 
        if user == args.user and filepath in filepaths:
            correlation_ids.append(props.correlation_id)
            consume_messages.add(message_id)
        else:
            reject_messages.add(message_id)
    except:
        reject_messages.add(message_id)

assert( len(messages) == len(consume_messages) + len(reject_messages) )

# Second loop
for message_id in consume_messages:  # Consuming
    channel.basic_ack(delivery_tag=message_id)
for message_id in reject_messages:  # Rejecting
    channel.basic_nack(delivery_tag=message_id)

connection.close()

print(len(correlation_ids), '!=', len(args.filepaths), file=sys.stderr)

if len(correlation_ids) != len(args.filepaths):
    sys.exit(2)

print(','.join(correlation_ids))
