import sys
import argparse
import uuid
import json
import pika
import logging

from lega.conf import CONF
from lega.utils.amqp import get_connection

LOG = logging.getLogger('publisher')

def make_user(args):
    msg = { "elixir_id": args.user }
    if args.password:
        msg['password_hash'] = args.password
    if args.pubkey:		
        msg['pubkey'] = args.pubkey
    return msg, 'sweden.user'

def make_file(args):
    return {
        'elixir_id': args.user,
        'filename': args.filename,
        'encrypted_integrity': { 'hash': args.encrypted_checksum, 'algorithm': args.encrypted_checksum_algo, },
        'unencrypted_integrity': { 'hash': args.unencrypted_checksum, 'algorithm': args.unencrypted_checksum_algo, },
    }, 'sweden.file'
    
def main():
    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser(description='Publish message to Central EGA broker.',
                                     allow_abbrev=False,
                                     epilog='The supported checksum algorithms are md5 and sha256')
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')

    subparsers = parser.add_subparsers(dest = 'user,file')
    subparsers.required=True

    files_parser = subparsers.add_parser("file", help="For a file submission")
    files_parser.add_argument('--user',                      required=True)
    files_parser.add_argument('--filename',                  required=True)
    files_parser.add_argument('--unencrypted_checksum',      required=True)
    files_parser.add_argument('--unencrypted_checksum_algo', default='md5', help='[Default: md5]')
    files_parser.add_argument('--encrypted_checksum',        required=True)
    files_parser.add_argument('--encrypted_checksum_algo',   default='md5', help='[Default: md5]')
    files_parser.set_defaults(func=make_file)

    users_parser = subparsers.add_parser("user", help="For the user inbox creation")
    users_parser.add_argument('--user',  required=True)
    users_parser.set_defaults(func=make_user)
    group = users_parser.add_mutually_exclusive_group(required=True)		
    group.add_argument('--pubkey')		
    group.add_argument('--password')

    args = parser.parse_args()

    params = { 'correlation_id': str(uuid.uuid4()),
             'content_type' : 'application/json',
             'delivery_mode': 2, # make message persistent
    }

    message, routing_key = args.func(args)

    connection = get_connection('cega.broker')
    channel = connection.channel()
    channel.basic_publish(exchange=CONF.get('cega.broker','exchange'),
                          routing_key=routing_key,
                          body=json.dumps(message),
                          properties=pika.BasicProperties(**params))

    connection.close()


if __name__ == '__main__':
    main()
