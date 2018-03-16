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

It is possible to start several workers.

When a message is consumed, it must be of the form:
* filepath
* target
* hash (of the unencrypted content)
* hash_algo: the associated hash algorithm
'''

import sys
import logging
from pathlib import Path
import uuid
import ssl
from functools import partial
from urllib.request import urlopen
import json


from .conf import CONF
from .utils import db, exceptions, checksum, sanitize_user_id
from .utils.amqp import consume, publish, get_connection
from .utils.crypto import ingest as crypto_ingest

LOG = logging.getLogger('ingestion')

@db.catch_error
def work(master_key, data):
    '''Main ingestion function

    The data is of the form:
    * user id
    * a filepath
    * encrypted hash information (with both the hash value and the hash algorithm)
    * unencrypted hash information (with both the hash value and the hash algorithm)

    The hash algorithm we support are MD5 and SHA256, for the moment.
    '''

    filepath = data['filepath']
    stable_id = data['stable_id']
    LOG.info(f"Processing {filepath} (with stable_id: {stable_id})")

    # Use user_id, and not elixir_id
    user_id = sanitize_user_id(data['user'])
    
    # Insert in database
    file_id = db.insert_file(filepath, user_id, stable_id)

    # early record
    internal_data = {
        'file_id': file_id,
        'user_id': user_id,
    }
    data['internal_data'] = internal_data

    # Find inbox
    inbox = Path( CONF.get('ingestion','inbox',raw=True) % { 'user_id': user_id } )
    LOG.info(f"Inbox area: {inbox}")

    # Check if file is in inbox
    inbox_filepath = inbox / filepath
    if not inbox_filepath.exists():
        raise exceptions.NotFoundInInbox(filepath) # return early

    # Ok, we have the file in the inbox
    # Get the checksums now

    try:
        encrypted_hash = data['encrypted_integrity']['checksum']
        encrypted_algo = data['encrypted_integrity']['algorithm']
    except KeyError:
        LOG.info('Finding a companion file')
        encrypted_hash, encrypted_algo = checksum.get_from_companion(inbox_filepath)
        data['encrypted_integrity'] = {'checksum': encrypted_hash,
                                       'algorithm': encrypted_algo }


    assert( isinstance(encrypted_hash,str) )
    assert( isinstance(encrypted_algo,str) )
    
    # Check integrity of encrypted file
    LOG.debug(f"Verifying the {encrypted_algo} checksum of encrypted file: {inbox_filepath}")
    if not checksum.is_valid(inbox_filepath, encrypted_hash, hashAlgo = encrypted_algo):
        LOG.error(f"Invalid {encrypted_algo} checksum for {inbox_filepath}")
        raise exceptions.Checksum(encrypted_algo, file=inbox_filepath, decrypted=False)
    LOG.debug(f'Valid {encrypted_algo} checksum for {inbox_filepath}')

    try:
        unencrypted_hash = data['unencrypted_integrity']['checksum']
        unencrypted_algo = data['unencrypted_integrity']['algorithm']
    except KeyError:
        # Strip the suffix first.
        LOG.info('Finding a companion file')
        unencrypted_hash, unencrypted_algo = checksum.get_from_companion(inbox_filepath.with_suffix(''))
        data['unencrypted_integrity'] = {'checksum': unencrypted_hash,
                                         'algorithm': unencrypted_algo }

    # Fetch staging area
    staging_area = Path( CONF.get('ingestion','staging') )
    LOG.info(f"Staging area: {staging_area}")
    #staging_area.mkdir(parents=True, exist_ok=True) # re-create
        
    # Create a unique name for the staging area
    unique_name = str(uuid.uuid5(uuid.NAMESPACE_OID, 'lega'))
    LOG.debug(f'Created an unique filename in the staging area: {unique_name}')
    staging_filepath = staging_area / unique_name

    # Save progress in database
    LOG.debug(f'Starting the re-encryption\n\tfrom {inbox_filepath}\n\tto {staging_filepath}')
    db.set_progress(file_id, str(staging_filepath), encrypted_hash, encrypted_algo, unencrypted_hash, unencrypted_algo)

    # Sending a progress message to CentralEGA
    data['status'] = { 'state': 'PROCESSING', 'details': None }
    LOG.debug(f'Sending message to CentralEGA: {data}')
    broker = get_connection('broker')
    publish(data, broker.channel(), 'cega', 'files.processing')

    # Decrypting
    cmd = CONF.get('ingestion','decrypt_cmd',raw=True) % { 'file': str(inbox_filepath) }
    LOG.debug(f'GPG command: {cmd}\n')
    details, staging_checksum = crypto_ingest( cmd,
                                               str(inbox_filepath),
                                               unencrypted_hash,
                                               hash_algo = unencrypted_algo,
                                               master_key = master_key,
                                               target = staging_filepath)
    db.set_encryption(file_id, details, staging_checksum)
    LOG.debug(f'Re-encryption completed')
    
    internal_data['filepath'] = str(staging_filepath)
    LOG.debug(f"Reply message: {data}")
    return data

def get_master_key():
    keyurl = CONF.get('ingestion','keyserver_endpoint_rsa')
    LOG.info(f'Retrieving the Master Public Key from {keyurl}')
    try:
        # Prepare to contact the Keyserver for the Master key
        with urlopen(keyurl) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        LOG.error(repr(e))
        LOG.critical('Problem contacting the Keyserver. Ingestion Worker terminated')
        sys.exit(1)


def main(args=None):
    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    master_key = get_master_key() # might exit

    LOG.info(f"Master Key ID: {master_key['id']}")
    LOG.debug(f"Master Key: {master_key}")
    do_work = partial(work, master_key)
        
    # upstream link configured in local broker
    consume(do_work, 'files', 'staged')

if __name__ == '__main__':
    main()
