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

parser.add_argument('queue', help='Queue from which to read')
parser.add_argument('routing_key', help='The routing key used for the CentralEGA exchange')
parser.add_argument('stable_id', help='Stable ID to add')

args = parser.parse_args()

# Connection
parameters = pika.URLParameters(args.connection)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

method_frame, header_frame, body = channel.basic_get(args.queue)
if method_frame:
    print(method_frame, header_frame, body)
    #channel.basic_ack(method_frame.delivery_tag)

# Just checking the JSON-formatting
data = json.loads(body)
checksum = None
for c in data['decrypted_checksums']:
    if c['type'].lower() == 'sha256':
        checksum = c['value']
        break
message = {
    'user': data['user'],
    'file_path': data['file_path'],
    'decrypted_checksums': [{ 'type': 'sha256', 'value': checksum }],
    'stable_id': args.stable_id,
}

print('Sending',message)

channel.basic_publish(exchange='localega.v1', routing_key=args.routing_key,
                      body=json.dumps(message),
                      properties=pika.BasicProperties(correlation_id=str(uuid.uuid4()),
                                                      content_type='application/json',
                                                      delivery_mode=2))

connection.close()
print('Message published to CentralEGA')

