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
import shutil

from .conf import CONF
from .utils import exceptions, sanitize_user_id
from .utils.db import insert_user
from .utils.amqp import get_connection, consume
from .utils.crypto import generate_key

LOG = logging.getLogger('inbox')

def create_homedir(user_id):
    '''Create a user home_folder and gives its ownership to root.

    Raises an exception in case of failure.'''
    LOG.info(f'Creating homedir for user {user_id}')

    assert( '@' not in user_id )
    homedir = CONF.get('inbox','home',raw=True) % { 'user_id': user_id }

    if not os.path.exists(homedir):
        skel = CONF.get('inbox','home_skel')
        LOG.debug(f'Creating {homedir} (from skeleton {skel})')
        shutil.copytree(skel,homedir, copy_function=shutil.copy) # no metadata
        # Note: ownership is already on root.
        # No metadata means that the setgid will make the folders ega group.
    else:
        LOG.debug(f'Homedir {homedir} already exists')

def work(data):
    '''Creates a user account, given the details from `data`.'''

    user_id = sanitize_user_id(data)
    password_hash = data.get('password_hash', None)
    pubkey = data.get('pubkey',None)
    assert password_hash or pubkey

    LOG.info(f'Handling account creation for user {user_id}')

    # Insert in database
    insert_user(user_id, password_hash, pubkey)

    # Create homefolder (might raise exception)
    create_homedir(user_id)

    LOG.info(f'Account created for user {user_id}')
    return data # return the same message

def main(args=None):

    if os.geteuid() != 0:
        print("You need to have root privileges to run this script. Exiting.", file=sys.stderr)
        sys.exit(1)

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    connection = get_connection('cega.broker')
    from_broker = (connection, CONF.get('cega.broker','user_queue'))
    to_broker = (connection, CONF.get('cega.broker','exchange'), CONF.get('cega.broker','user_routing'))
    consume(from_broker, work, to_broker)

if __name__ == '__main__':
    main()
