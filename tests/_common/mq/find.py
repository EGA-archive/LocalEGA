#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads all messages from a queue and dumps the one with given
correlation id to stdout, if found"""

import sys
import json
import argparse
import os

import pika

# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--connection', help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'")
parser.add_argument('queue', help='The queue to listen to')
parser.add_argument('correlation_id', help="Fetch a given correlation id")
args = parser.parse_args()

# MQ Connection
mq_connection = args.connection if args.connection else os.getenv('CEGA_CONNECTION', default="amqp://localhost:5672/%2F")
parameters = pika.URLParameters(mq_connection)
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
