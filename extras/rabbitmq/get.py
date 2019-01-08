#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads all messages from a queue and fetches the correlation_id for the one with given path, if found"""

import sys
import json
import argparse

import pika

# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--connection', help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'", default='amqp://localhost:5672/%2F')
parser.add_argument('--latest_message', action='store_true')
parser.add_argument('queue', help="Queue to read")
parser.add_argument('checksum', help="File to search for")
args = parser.parse_args()

# MQ Connection
parameters = pika.URLParameters(args.connection)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

correlation_ids = []
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
        integrity = data.get('encrypted_integrity')
        if integrity:
            checksum = integrity.get('checksum')
            if checksum == args.checksum:
                correlation_ids.append( (props.correlation_id,message_id) )
    except:
        pass


# Second loop, nack the messages
for message_id in messages:
    channel.basic_nack(delivery_tag=message_id)

connection.close()

if not correlation_ids:
    sys.exit(2)

correlation_id = correlation_ids[0][0]
if args.latest_message:
    message_id = -1  # message ids are positive
    for cid, mid in correlation_ids:
        if mid > message_id:
            correlation_id = cid
print(correlation_id)
