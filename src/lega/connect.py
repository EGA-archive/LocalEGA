#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Connecting to Central EGA to Local EGA
#
####################################

Connects to message broker A,
picks a message and
re-publish it in message broker B.
'''

import sys
import logging
import argparse

from .conf import CONF
from . import db
from .utils.amqp import get_connection, forward

LOG = logging.getLogger('connect')

def set_file_id(data):
    '''Adding the related file into the database
    and adding the return file id into the message'''

    filename = data['filename']
    elixir_id = data['elixir_id']
    enc_checksum  = data['encrypted_integrity']
    org_checksum  = data['unencrypted_integrity']

    # Find user_id
    user_id = db.get_user(elixir_id)

    # Insert in database
    file_id = db.insert_file(filename, enc_checksum, org_checksum, user_id) 
    assert file_id is not None, 'Ouch...database problem!'
    LOG.debug(f'Created id {file_id} for {data["filename"]}')

    data['file_id'] = file_id
    data['user_id'] = user_id
    return data

def set_user_id(data):
    '''Adding the user into the database
    and updating the return user id into the message'''

    elixir_id = data['elixir_id']
    password_hash = data.get('password_hash', None)
    pubkey = data.get('pubkey',None)
    # Insert in database
    user_id = db.insert_user(elixir_id, password_hash, pubkey)
    assert user_id is not None, 'Ouch...database problem!'
    LOG.debug(f'Created id {user_id} for user {elixir_id}')
    data['user_id'] = user_id
    return data

def main():
    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser(description="Forward message between CentralEGA's broker and the local one",
                                     allow_abbrev=False)
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')
    parser.add_argument('--transform', default=None)

    group_in = parser.add_argument_group(title='Arguments for the incoming connection')
    group_in.add_argument('from_domain')
    group_in.add_argument('from_queue')
    group_out = parser.add_argument_group(title='Arguments for the outgoing connection')
    group_out.add_argument('to_domain')
    group_out.add_argument('to_exchange')
    group_out.add_argument('to_routing')

    args = parser.parse_args()

    LOG.info(f'Connection {args.from_domain} to {args.to_domain}')
    LOG.debug(f'From queue: {args.from_queue}')
    LOG.debug(f'To exchange: {args.to_exchange}')
    LOG.debug(f'To routing key: {args.to_routing}')

    transform = None
    if args.transform:
        transform = getattr(sys.modules[__name__], args.transform, None)
    if transform:
        LOG.debug(f'Transform function: {transform}')

    from_connection = get_connection(args.from_domain)
    from_channel = from_connection.channel()

    to_connection = get_connection(args.to_domain)
    to_channel = to_connection.channel()
    to_channel.basic_qos(prefetch_count=1) # One job at a time

    LOG.info(f'Forwarding messages')

    try:
        forward(from_channel,
                from_queue  = args.from_queue,
                to_channel  = to_channel,
                to_exchange = args.to_exchange,
                to_routing  = args.to_routing,
                transform   = transform)
    except KeyboardInterrupt:
        from_channel.stop_consuming()
    finally:
        to_connection.close()
        to_connection.close()

if __name__ == '__main__':
    main()
