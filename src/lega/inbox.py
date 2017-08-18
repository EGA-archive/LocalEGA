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
from .utils import db, exceptions
from .utils import catch_user_error, generate_password
from .utils.amqp import get_connection, consume
from .utils.crypto import generate_key

LOG = logging.getLogger('inbox')

def create_account(user_id, comment=None):
    '''Create a user account and changes its home folder to be owned by root.

    The home folder is specified in the /etc/default/useradd
    Raises an exception in case of failure.
    
    Note: It does not check if the account already exists.'''
    assert( isinstance(user_id,int) )
    LOG.info(f'Creating account for user {user_id}')
    create_cmd = ['useradd','-u',str(user_id),'-g',CONF.get('inbox','ega_group')]

    home = CONF.get('inbox','home',fallback=None)
    if home:
        create_cmd.extend(['-m','-d',home])

    if comment:
        create_cmd.extend(['--comment', comment])

    create_cmd.append(str(user_id))

    LOG.debug(f'Create cmd: {create_cmd}')

    subprocess.run(create_cmd, check=True, stderr = subprocess.DEVNULL)

    LOG.debug('Making its home folder owned by root')
    real_home = getpwuid(user_id).pw_dir # gets the actual home dir
    os.chown(real_home, 0, -1) # owned by root, but don't change group id
    return real_home

def update_password(user_id, password_hash):
    '''Updates a given user's password.'''
    assert(password_hash)
    LOG.info(f'Updating password for user {user_id} with {password_hash}')
    subprocess.run(['chpasswd','-e'],
                   input=f'{user_id}:{password_hash}'.encode(), # bytes passed to the subprocess's stdin
                   check=True, # raise exception on error
                   stderr = subprocess.DEVNULL)

def delete_account(user_id):
    LOG.info(f'Deleting account for user {user_id}')
    try:
        user_home = getpwuid(user_id).pw_dir # check first
        delete_cmd = ['userdel','-r', str(user_id)]
        LOG.debug(f'Delete cmd: {delete_cmd}')
        subprocess.run(delete_cmd, stderr = subprocess.DEVNULL, check=False) # do not check for errors
        # remove the folder (cuz owned by root)
        LOG.debug(f'Removing tree: {user_home}')
        shutil.rmtree(user_home, ignore_errors=True)
    except KeyError:
        LOG.error(f'User {user_id} not found')

def update_pubkey(user_id, pubkey):
    group_id = getpwuid(user_id).pw_gid
    gid = getgrnam(CONF.get('inbox','ega_group')).gr_gid
    assert( group_id == gid )
    LOG.info(f'Updating public key for user {user_id}')
    ssh_dir = Path(getpwuid(user_id).pw_dir) / '.ssh'
    ssh_dir.mkdir(mode=0o700, parents=False, exist_ok=True)
    os.chown(str(ssh_dir), user_id, group_id)
    authorized_file = str(ssh_dir / 'authorized_keys')
    with open(authorized_file, 'w') as ssh_keys: # we are root
        ssh_keys.write(pubkey) # no \n
        os.chown(authorized_file, user_id, group_id)
        os.chmod(authorized_file, 0o600)


@catch_user_error
def work(data):
    '''Creates a user account, given the details from `data`.'''

    user_id = int(data['user_id'])
    elixir_id = data['elixir_id']
    password_hash = data.get('password_hash', None)
    pubkey = data.get('pubkey',None)
    assert password_hash or pubkey

    LOG.info(f'Handling account creation for user {elixir_id}')

    # Create user (might raise exception)
    delete_account(user_id) # delete first
    user_home = create_account(user_id, comment = elixir_id)

    # Set public key
    if pubkey:
        update_pubkey(user_id, pubkey)
    else:
        LOG.info('No public key supplied')
        
    # Set password
    if password_hash:
        update_password(user_id, password_hash)
    else:
        LOG.info('No password supplied')


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
