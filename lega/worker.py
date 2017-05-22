#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Re-Encryption Worker
#
####################################

It simply consumes message from the message queue configured in the [worker] section of the configuration files.

It defaults to the `tasks` queue.

It is possible to start several workers, of course!
However, they should have the gpg-agent socket location in their environment (when using GnuPG 2.0 or less).
In GnuPG 2.1, it is not necessary (Just point the `homedir` to the right place).

When a message is consumed, it must be of the form:
* filepath
* target
* hash (of the unencrypted content)
* hash_algo: the associated hash algorithm
'''

import sys
import os
import logging
import json
from pathlib import Path
import shutil
import stat

from .conf import CONF
from . import crypto
from . import amqp as broker
from . import db
from .utils import (
    get_data as parse_data,
    get_inbox,
    get_staging_area,
    checksum
)

LOG = logging.getLogger('worker')

def work(data):
    '''Main ingestion function

    The data is of the form:
    * user id
    * a filename
    * encrypted hash information (with both the hash value and the hash algorithm)
    * unencrypted hash information (with both the hash value and the hash algorithm)

    The hash algorithm we support are MD5 and SHA256, for the moment.
    '''

    user_id = data['user_id']

    # Find inbox
    inbox = Path( CONF.get('worker','inbox',raw=True) % { 'user_id': user_id } )
    LOG.info(f"Inbox area: {inbox}")

    # Create staging area for user
    staging_area = Path( CONF.get('worker','staging',raw=True) % { 'user_id': user_id } )
    LOG.info(f"Staging area: {staging_area}")
    shutil.rmtree(staging_area, ignore_errors=True) # delete
    staging_area.mkdir(parents=True, exist_ok=True) # re-create

    filename = data['filename']
    LOG.info(f"Processing {filename}")

    # Insert in database
    file_id = db.insert_file(filename  = filename,
                             enc_checksum  = data['encrypted_integrity'],
                             org_checksum  = data['unencrypted_integrity'],
                             user_id = user_id)
        
    LOG.debug(f'Created id {file_id} for {data["filename"]}')
    assert file_id is not None, 'Ouch...database problem!'

    inbox_filepath = inbox / filename
    staging_filepath = staging_area / filename

    if not inbox_filepath.exists():
        db.set_error(file_id, exceptions.NotFoundInInbox(filename))
        return None # return early

    # Get permissions
    permissions = oct(inbox_filepath.stat().st_mode)[-3:]

    # Ok, we have the file in the inbox
    try:

        filehash = data['encrypted_integrity']['hash']
        hash_algo = data['encrypted_integrity']['algorithm']

        assert( isinstance(filehash,str) )
        assert( isinstance(hash_algo,str) )
    
        ################# Check integrity of encrypted file
        LOG.debug(f"Verifying the {hash_algo} checksum of encrypted file: {inbox_filepath}")
        with open(inbox_filepath, 'rb') as inbox_file: # Open the file in binary mode. No encoding dance.
            if not checksum(inbox_file, filehash, hashAlgo = hash_algo):
                errmsg = f"Invalid {hash_algo} checksum for {inbox_filepath}"
                LOG.warning(errmsg)
                raise exceptions.Checksum(filename)
        LOG.debug(f'Valid {hash_algo} checksum for {inbox_filepath}')

        ################# Locking the file in the inbox
        LOG.debug(f'Locking the file {inbox_filepath}')
        inbox_filepath.chmod(stat.S_IRUSR) # 400: Remove write permissions

        unencrypted_hash = data['unencrypted_integrity']['hash']
        unencrypted_algo = data['unencrypted_integrity']['algorithm']
        
        LOG.debug(f'Starting the re-encryption\n\tfrom {inbox_filepath}\n\tto {staging_filepath}')
        db.update_status(file_id, db.Status.In_Progress)
        details, reenc_key = crypto.ingest( str(inbox_filepath),
                                            unencrypted_hash,
                                            hash_algo = unencrypted_algo,
                                            target = staging_filepath)
        db.set_encryption(file_id, details, reenc_key)
        LOG.debug(f'Re-encryption completed')
        reply = {
            'file_id' : file_id,
            'filepath': str(staging_filepath),
            'target_name': f"{unencrypted_algo}__{unencrypted_hash}",
            'user_id': user_id,
        }
        LOG.debug(f"Reply message: {reply!r}")
        db.notify_vault(json.dumps(reply))

    except Exception as e:
        if isinstance(e,AssertionError):
            raise e
        errmsg = f'{e.__class__.__name__}: {e!s} | user id: {user_id}'
        LOG.error(errmsg)
        # Restore permissions
        inbox_filepath.chmod(permissions)
        db.set_error(file_id, e)


def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    connection = broker.get_connection('cega.broker')
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        broker.consume( channel,
                        work,
                        from_queue = CONF.get('cega.broker','queue'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
