import pika
import sys
import argparse
import urllib.parse
import ssl
import logging
import uuid
import json

from .conf import CONF
from . import amqp as broker

LOG = logging.getLogger('publisher')

def main():
    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser(description='Publish message to Central EGA broker.')
    parser.add_argument('--user', action='store')
    parser.add_argument('--filename', action='store')
    parser.add_argument('--unencrypted_checksum', action='store')
    parser.add_argument('--unencrypted_checksum_algo', action='store', default='md5')
    parser.add_argument('--encrypted_checksum', action='store')
    parser.add_argument('--encrypted_checksum_algo', action='store', default='md5')
    parser.add_argument('--conf', action='store')
    args = parser.parse_args()

    connection = broker.get_connection('cega.broker')
    channel = connection.channel()

    params = { 'correlation_id': str(uuid.uuid4()),
             'content_type' : 'application/json',
             'delivery_mode': 2, # make message persistent
    }

    message = {
        'user_id': args.user,
        'filename': args.filename,
        'encrypted_integrity': { 'hash': args.encrypted_checksum, 'algorithm': args.encrypted_checksum_algo, },
        'unencrypted_integrity': { 'hash': args.unencrypted_checksum, 'algorithm': args.unencrypted_checksum_algo, },
    }

    channel.basic_publish(exchange=CONF.get('cega.broker','exchange'),
                          routing_key='sweden.file',
                          body=json.dumps(message),
                          properties=pika.BasicProperties(**params))

    connection.close()


if __name__ == '__main__':
    main()
