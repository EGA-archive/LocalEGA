import sys
import argparse
import uuid
import json
import pika

from .conf import CONF
from . import amqp as broker

def main():
    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser(description='Publish message to Central EGA broker.',
                                     allow_abbrev=False,
                                     epilog='The supported checksum algorithms are md5 and sha256')
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')

    group = parser.add_argument_group(title='Compulsary components for a published message')
    group.add_argument('--user',                      required=True)
    group.add_argument('--filename',                  required=True)
    group.add_argument('--unencrypted_checksum',      required=True)
    group.add_argument('--unencrypted_checksum_algo', default='md5', help='[Default: md5]')
    group.add_argument('--encrypted_checksum',        required=True)
    group.add_argument('--encrypted_checksum_algo',   default='md5', help='[Default: md5]')

    args = parser.parse_args()

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

    connection = broker.get_connection('cega.broker')
    channel = connection.channel()
    channel.basic_publish(exchange=CONF.get('cega.broker','exchange'),
                          routing_key='sweden.file',
                          body=json.dumps(message),
                          properties=pika.BasicProperties(**params))

    connection.close()


if __name__ == '__main__':
    main()
