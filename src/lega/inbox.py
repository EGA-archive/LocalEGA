#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Service creating the inboxes
#
####################################

It picks a message from a local queue, containing information about a user.

It inserts it in the database and creates the necessary location in the inbox server.
'''

import sys
import os
import logging
import subprocess
from pathlib import Path

from .conf import CONF
from .utils import db, exceptions
from .utils import catch_user_error, generate_password
from .utils.amqp import get_connection, consume
from .utils.crypto import generate_key

LOG = logging.getLogger('inbox')


@catch_user_error
def work(data):
    '''Creates a user account, given the details from `data`.
    '''

    user_id = int(data['user_id'])
    elixir_id = data['elixir_id']
    password_hash = data.get('password_hash', None)
    pubkey = data.get('pubkey',None)
    assert password_hash or pubkey

    LOG.info(f'Handling account creation for user {elixir_id}')

    user_home = Path( CONF.get('inbox','user_home',raw=True) % { 'user_id': user_id } )

    # Create user (might raise exception)
    delete_cmd = CONF.get('inbox','delete_account',raw=True) # should we sanitize first?
    subprocess.run(delete_cmd.format(home=user_home,user_id=user_id),
                   shell=True,
                   check=False, # do not check for errors
                   stderr = subprocess.DEVNULL)

    create_cmd = CONF.get('inbox','create_account',raw=True) # should we sanitize first?
    subprocess.run(create_cmd.format(home=user_home,comment=elixir_id,user_id=user_id),
                   shell=True,
                   check=True,
                   stderr = subprocess.DEVNULL)

    os.chown(str(user_home), 0, -1) # owned by root, but don't change group id

    # Set public key
    if pubkey:
        authorized_keys = user_home / '.pubkey'
        with open(authorized_keys, 'w') as ssh_keys: # we are root
            ssh_keys.write(pubkey)
            ssh_keys.write('\n')
            os.chown(str(authorized_keys),user_id, -1)
            authorized_keys.chmod(0o600)

    # Set password
    if password_hash:
        password_cmd = CONF.get('inbox','update_password',raw=True) # should we sanitize first?
        subprocess.run(password_cmd.format(user_id=user_id,password_hash=password_hash),
                       shell=True,
                       check=True,
                       stderr = subprocess.DEVNULL)

    LOG.info(f'Account created for user {elixir_id}')
    return {
        'user_id': user_id,
        'elixir_id': elixir_id,
        # 'pubkey' : pubkey,
        # 'seckey': seckey,
        # 'password': password,
    }

def main(args=None):

    if os.geteuid() != 0:
        print("You need to have root privileges to run this script. Exiting.", file=sys.stderr)
        sys.exit(1)

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    LOG.info('Starting a connection to the local broker')

    connection = get_connection('local.broker')
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        consume(channel,
                work,
                from_queue  = CONF.get('local.broker','users_queue'),
                to_channel  = channel,
                to_exchange = CONF.get('local.broker','exchange'),
                to_routing  = CONF.get('local.broker','routing_account'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
