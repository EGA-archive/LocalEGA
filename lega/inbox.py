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
import stat
import pwd

from .conf import CONF
from . import exceptions
from . import amqp as broker
from . import db

LOG = logging.getLogger('inbox')

def work(data):
    '''Creates a user account, given the details from `data`.
    '''

    user = data.get('elixir_id',None)
    password = data.get('password', None)
    pubkey = data.get('pubkey', None)
    assert user, "We need an elixir-id"
    assert (password or pubkey), "We need either a password or a public key"

    # Temporary there until we have a deployment strategy
    if CONF.getboolean('inbox','test'):
        return

    user_home = Path( CONF.get('inbox','user_home',raw=True) % { 'user': user } )
    
    # first create user_dir and do nothing if it exists already
    try:
        user_home.mkdir(mode=0o700)
    except OSError as e:
        user_home.chmod(mode=stat.S_IRWXU) # rwx------ 700

    # home dir need to be owned by root for chroot to work
    os.chown(str(user_home), 0, 0) # owned by root

    try:
        cmd = CONF.get('inbox','cmd',raw=True) # should we sanitize first?
        subprocess.run(cmd.format(home=user_home,comment=user,user=user), shell=True, check=True)
    except (subprocess.CalledProcessError, KeyError) as e:
        raise exceptions.InboxCreationError(f'Inbox creation failed for {user}: {e}')
    
    # set password
    if password:
        os.system(f'echo "{user}:{password}" | chpasswd -e') # should definitely sanitize!
    else:
        os.system(f'usermod -p "*" {user}') # disable password

    # a sub-directory of user home - since the chrooted user home
    # need to be owned by root and not have user write access
    try:
        inbox = str(user_home / 'inbox')
        uid = pwd.getpwnam(user).pw_uid
        os.chown(inbox, uid, -1)
    except OSError as e:
        raise exceptions.InboxCreationError(f'Inbox creation failed for {user}: {e}')


def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    LOG.info('Starting a connection to the local broker')

    connection = broker.get_connection('local.broker')
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        broker.consume(channel,
                       work,
                       from_queue  = CONF.get('local.broker','users_queue'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
