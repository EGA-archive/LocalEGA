#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Consumes message from a queue and dumps them to stdout."""

import pika
import json
import argparse

# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--connection', help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'", default='amqp://localhost:5672/%2F')
parser.add_argument('queue', help='The queue to listen to')
args = parser.parse_args()

# MQ Connection
parameters = pika.URLParameters(args.connection)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# For each message
def process_request(channel, method_frame, props, body):
    correlation_id = props.correlation_id
    message_id = method_frame.delivery_tag
    try:
        data = json.loads(body)
    except:
        data = {'non-json message' : body.decode()}

    res = [str(correlation_id), str(message_id)]
    for k,v in data.items():
        res.append(f'{k}: {v}')
    message = '\t'.join(res)
    print(message)  # Print to stdout

    # Ack the message
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

# Let's do this
try:
    channel.basic_consume(process_request, queue=args.queue)
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()
finally:
    connection.close()
