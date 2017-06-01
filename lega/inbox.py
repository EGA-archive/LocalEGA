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

from .conf import CONF
from . import amqp as broker
from . import db

LOG = logging.getLogger('inbox')

def work(data):
    '''
    '''

    user = data.get('elixir_id',None)
    password = data.get('password', None)
    pubkey = data.get('pubkey', None)
    assert user, "We need an elixir-id"
    assert (password or pubkey), "We need either a password or a public key"


    # db.insert_user(user_id = user,
    #                password = password,
    #                pubkey = pubkey)

    user_home = Path( CONF.get('inbox','user_home',raw=True) % { 'user': user } )
    
    # first create user_dir and do nothing if it exists already
    try:
        user_home.mkdir(mode=0o700)
    except OSError as e:
        user_home.chmod(mode=stat.IRWXU) # rwx------ 700

    # home dir need to be owned by root for chroot to work
    user_home.chown(0, 0) # owned by root

    try:
        subprocess.run(f'useradd -M --home {user_home} --comment "{user},,," "{user}"', # should we sanitize first?
                       check=True)
    except subprocess.CalledProcessError as e:
        raise exceptions.InboxCreationError(f'Inbox creation failed for {user}')
    
    # set password
    if password:
        os.system(f'echo "{user}:{passwd}" | chpasswd -e')
     
    # a sub-directory of user home - since the chrooted user home
    # need to be owned by root and not have user write access
    try:
        inbox = user_home / 'inbox'
        uid = pwd.getpwnam(user).pw_uid
        inbox.chown(uid, gid)
    except OSError as e:
        pass


def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

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
