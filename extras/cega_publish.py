#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''Publishing a message to CentralEGA, given a routing key.'''

import argparse
import uuid
import json
import string
import secrets

import pika

parser = argparse.ArgumentParser(description='''Publish message to the broker on this machine.''')

parser.add_argument('--connection',
                    help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'",
                    default='amqp://localhost:5672/%2F')

parser.add_argument('routing_key', help='The routing key used for the CentralEGA exchange')
parser.add_argument('message', help='A JSON-formatted string')

args = parser.parse_args()

# Just checking the JSON-formatting
message = json.loads(args.message)

parameters = pika.URLParameters(args.connection)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.basic_publish(exchange='localega.v1', routing_key=args.routing_key,
                      body=json.dumps(message),
                      properties=pika.BasicProperties(correlation_id=str(uuid.uuid4()),
                                                      content_type='application/json',
                                                      delivery_mode=2))

connection.close()
print('Message published to CentralEGA')

