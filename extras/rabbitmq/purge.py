#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''Consumes messages from the specified broker. Effectively reseting the queues.'''

import argparse

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
                    help="of the form 'amqp://<user>:<password>@<host>:<port>/<vhost>'",
                    default='amqp://localhost:5672/%2F')

parser.add_argument('--queues', 
                    help='Comma-separated list of queues to consume from',
                    default=','.join(hellgate_queues))

args = parser.parse_args()

parameters = pika.URLParameters(args.connection)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

for queue in args.queues.split(','):
    channel.queue_purge(queue=queue)
    print('Clean slate for',queue)

connection.close()
