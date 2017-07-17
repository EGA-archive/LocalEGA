import sys
import argparse
import uuid
import json
import pika
import logging

from .conf import CONF
from .utils.amqp import get_connection

LOG = logging.getLogger('publisher')

def make_user(args):
    msg = { "elixir_id": args.name }
    if args.password:
        msg['password_hash'] = args.password
    if args.pubkey:		
        msg['pubkey'] = args.pubkey
    return msg

def make_file(args):
    return {
        'elixir_id': args.user,
        'filename': args.filename,
        'encrypted_integrity': { 'hash': args.encrypted_checksum, 'algorithm': args.encrypted_checksum_algo, },
        'unencrypted_integrity': { 'hash': args.unencrypted_checksum, 'algorithm': args.unencrypted_checksum_algo, },
    }
    
def main():
    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser(description='Publish message to a given broker.',
                                     allow_abbrev=False,
                                     add_help=False)

    common_parser = argparse.ArgumentParser(add_help=False)                                 
    common_parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    common_parser.add_argument('--log',  help='configuration file for the loggers')
    common_parser.add_argument('--broker',  help='Broker section in the conf file [Default: cega.broker]', default='cega.broker')
    common_parser.add_argument('--routing',  help='Where to publish the message', required=True)
    
    subparsers = parser.add_subparsers(title='Choose between submitting a file or a user', 
                                       help='For a file submission or a user inbox creation')
    subparsers.required=True

    files_parser = subparsers.add_parser("file", epilog='The supported checksum algorithms are md5 and sha256', parents=[common_parser])
    files_parser.set_defaults(func=make_file)
    files_parser.add_argument('user')
    files_parser.add_argument('filename')
    unenc_group = files_parser.add_argument_group('unencrypted checksum')
    unenc_group.add_argument('--unencrypted_checksum', required=True)
    unenc_group.add_argument('--unencrypted_checksum_algo', default='md5', help='[Default: md5]')
    enc_group = files_parser.add_argument_group('encrypted checksum')
    enc_group.add_argument('--encrypted_checksum', required=True)
    enc_group.add_argument('--encrypted_checksum_algo',   default='md5', help='[Default: md5]')

    users_parser = subparsers.add_parser("user", parents=[common_parser])
    users_parser.set_defaults(func=make_user)
    users_parser.add_argument('name')
    users_parser.add_argument('pubkey')
    users_parser.add_argument('password')

    args = parser.parse_args()

    params = { 'correlation_id': str(uuid.uuid4()),
             'content_type' : 'application/json',
             'delivery_mode': 2, # make message persistent
    }

    message = args.func(args)

    connection = get_connection(args.broker)
    channel = connection.channel()
    channel.basic_publish(exchange=CONF.get(args.broker,'exchange'),
                          routing_key=args.routing,
                          body=json.dumps(message),
                          properties=pika.BasicProperties(**params))

    connection.close()


if __name__ == '__main__':
    main()
