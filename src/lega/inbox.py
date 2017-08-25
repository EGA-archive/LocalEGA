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
import shutil
from pwd import getpwuid
from grp import getgrnam

from .conf import CONF
from .utils import exceptions
from .utils import catch_user_error, generate_password
from .utils.db import insert_user
from .utils.amqp import get_connection, consume
from .utils.crypto import generate_key

LOG = logging.getLogger('inbox')

def create_homedir(user_id):
    '''Create a user home_folder and gives its ownership to root.

    Raises an exception in case of failure.'''
    LOG.info(f'Creating homedir for user {user_id}')

    home = CONF.get('inbox','home')
    if not home:
        raise exceptions.InboxCreationError('home settings not set in [inbox]')

    assert( '@' not in user_id )
    homedir = Path(home) / user_id
    
    LOG.debug(f'Creating {homedir}')
    homedir.mkdir(mode=0o770, parents=False, exist_ok=True) # Parents should be there

    LOG.debug('Making its home folder owned by root')
    os.chown(str(homedir), 0, -1) # owned by root, but don't change group id

@catch_user_error
def work(data):
    '''Creates a user account, given the details from `data`.'''

    user_id = data['user_id']
    password_hash = data.get('password_hash', None)
    pubkey = data.get('pubkey',None)
    assert password_hash or pubkey

    LOG.info(f'Handling account creation for user {user_id}')

    # Insert in database
    internal_id = insert_user(user_id, password_hash, pubkey)
    assert internal_id is not None, 'Ouch...database problem!'
    LOG.debug(f'User {user_id} added to the database (as entry {internal_id}).')

    # Create homefolder (might raise exception)
    create_account(user_id)

    LOG.info(f'Account created for user {user_id}')
    return data # return the same message

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
