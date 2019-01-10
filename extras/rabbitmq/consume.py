#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Consumes the first message from a queue, if the user+filepath match"""

import sys
import json
import argparse

import pika

# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--connection', help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'", default='amqp://localhost:5672/%2F')
parser.add_argument('queue', help="Queue to read")
parser.add_argument('user')
parser.add_argument('filepath')
args = parser.parse_args()

# MQ Connection
parameters = pika.URLParameters(args.connection)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

correlation_id = None
messages = set()

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
        if user == args.user and filepath == args.filepath:
            correlation_id = props.correlation_id
            channel.basic_ack(delivery_tag=message_id)
            messages.remove(message_id)
            break
    except:
        pass

# Second loop, nack the remaining messages
for message_id in messages:
    channel.basic_nack(delivery_tag=message_id)

connection.close()

if correlation_id is None:
    sys.exit(2)

print(correlation_id)
