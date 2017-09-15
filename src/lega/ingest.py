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
from pathlib import Path
import shutil
import stat
import uuid
from multiprocessing import Process, cpu_count
import ssl
from functools import partial
from pgpy import PGPKey
from Cryptodome.PublicKey import RSA

from .conf import CONF
from .utils import db, exceptions, checksum
from .utils.amqp import get_connection, consume
from .utils.crypto import ingest as crypto_ingest
from .keyserver import get_ingestion_keys

LOG = logging.getLogger('ingestion')

@db.catch_error
def work(pgp_seckey, pgp_passphrase, master_pubkey, data):
    '''Main ingestion function

    The data is of the form:
    * user id
    * a filename
    * encrypted hash information (with both the hash value and the hash algorithm)
    * unencrypted hash information (with both the hash value and the hash algorithm)

    The hash algorithm we support are MD5 and SHA256, for the moment.
    '''

    filename = data['filename']
    LOG.info(f"Processing {filename}")

    # Use user_id, and not elixir_id
    user_id = sanitize_user_id(data)

    # Insert in database
    file_id = db.insert_file(filename, user_id)
    data['file_id'] = file_id

    # Find inbox
    inbox = Path( CONF.get('ingestion','inbox',raw=True) % { 'user_id': user_id } )
    LOG.info(f"Inbox area: {inbox}")

    # Check if file is in inbox
    inbox_filepath = inbox / filename
    if not inbox_filepath.exists():
        raise exceptions.NotFoundInInbox(filename) # return early

    # Ok, we have the file in the inbox
    # Get the checksums now

    try:
        encrypted_hash = data['encrypted_integrity']['hash']
        encrypted_algo = data['encrypted_integrity']['algorithm']
    except KeyError:
        LOG.info('Finding a companion file')
        encrypted_hash, encrypted_algo = checksum.get_from_companion(inbox_filepath)


    assert( isinstance(encrypted_hash,str) )
    assert( isinstance(encrypted_algo,str) )
    
    # Check integrity of encrypted file
    LOG.debug(f"Verifying the {encrypted_algo} checksum of encrypted file: {inbox_filepath}")
    if not checksum.is_valid(inbox_filepath, encrypted_hash, hashAlgo = encrypted_algo):
        LOG.error(f"Invalid {encrypted_algo} checksum for {inbox_filepath}")
        raise exceptions.Checksum(encrypted_algo, f'for {inbox_filepath}')
    LOG.debug(f'Valid {encrypted_algo} checksum for {inbox_filepath}')

    # Fetch staging area
    staging_area = Path( CONF.get('ingestion','staging') )
    LOG.info(f"Staging area: {staging_area}")
    #staging_area.mkdir(parents=True, exist_ok=True) # re-create
        
    # Create a unique name for the staging area
    #unique_name = str(uuid.uuid4())
    unique_name = str(uuid.uuid5(uuid.NAMESPACE_OID, 'lega'))
    LOG.debug(f'Created an unique filename in the staging area: {unique_name}')
    staging_filepath = staging_area / unique_name

    try:
        unencrypted_hash = data['unencrypted_integrity']['hash']
        unencrypted_algo = data['unencrypted_integrity']['algorithm']
    except KeyError:
        # Strip the suffix first.
        LOG.info('Finding a companion file')
        unencrypted_hash, unencrypted_algo = checksum.get_from_companion(inbox_filepath.with_suffix(''))

    LOG.debug(f'Starting the re-encryption\n\tfrom {inbox_filepath}\n\tto {staging_filepath}')
    db.set_progress(file_id, str(staging_filepath), encrypted_hash, encrypted_algo, unencrypted_hash, unencrypted_algo)
    details, staging_checksum = crypto_ingest( str(inbox_filepath),
                                               unencrypted_hash,
                                               hash_algo = unencrypted_algo,
                                               pgp_key=pgp_seckey,
                                               pgp_passphrase=pgp_passphrase,
                                               master_key=master_pubkey,
                                               target = staging_filepath)
    db.set_encryption(file_id, details, staging_checksum)
    LOG.debug(f'Re-encryption completed')

    reply = {
        'file_id' : file_id,
        'filepath': str(staging_filepath),
        'user_id': user_id,
    }
    LOG.debug(f"Reply message: {reply!r}")
    return reply

def main(args=None):
    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    # Prepare to contact the Keyserver for the PGP key
    host = CONF.get('ingestion','keyserver_host')
    port = CONF.getint('ingestion','keyserver_port')
    ssl_certfile = Path(CONF.get('ingestion','keyserver_ssl_certfile')).expanduser()

    ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ssl_certfile) if (ssl_certfile and ssl_certfile.exists()) else None

    if not ssl_ctx:
        LOG.error('No SSL encryption. Exiting...')
        sys.exit(2)
    else:
        LOG.info('With SSL encryption')

    try:
        LOG.info('Retrieving keys')
        # Retrieve the keys
        pgp_private_keyblob, pgp_passphrase, master_public_keyblob = get_ingestion_keys(host, port, ssl=ssl_ctx)

        # Might raise exception
        pgp_seckey, _ = PGPKey.from_blob(pgp_private_keyblob) # Not unlocked yet
        master_pubkey = RSA.import_key(master_public_keyblob) # Public key: No passphrase

    except Exception as e:
        LOG.error(repr(e))
        LOG.critical('Problem contacting the Keyserver. Ingestion Worker terminated')
        sys.exit(1)
    else:
        from_broker = (get_connection('cega.broker'), CONF.get('cega.broker','file_queue'))
        to_broker = (get_connection('local.broker'), 'lega', 'lega.complete')
        consume(from_broker, work, to_broker)

if __name__ == '__main__':
    main()
