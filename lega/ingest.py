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
import uuid
import ssl
from functools import partial
import asyncio

from Cryptodome.PublicKey import RSA

from .conf import CONF
from .utils import db, exceptions, checksum, sanitize_user_id
from .utils.amqp import consume, publish, get_connection
from .utils.crypto import ingest as crypto_ingest
from .keyserver import MASTER_PUBKEY, ACTIVE_MASTER_KEY

LOG = logging.getLogger('ingestion')

async def _req(req, host, port, ssl=None, loop=None):
    reader, writer = await asyncio.open_connection(host, port, ssl=ssl, loop=loop)

    try:
        LOG.debug(f"Sending request for {req}")
        # What does the client want
        writer.write(req)
        await writer.drain()

        LOG.debug("Waiting for answer")
        buf=bytearray()
        while True:
            data = await reader.read(1000)
            if data:
                buf.extend(data)
            else:
                writer.close()
                LOG.debug("Got it")
                return buf
    except Exception as e:
        LOG.error(repr(e))
        writer.write(repr(e))
        await writer.drain()
        writer.close()

@db.catch_error
def work(active_master_key, master_pubkey, data):
    '''Main ingestion function

    The data is of the form:
    * user id
    * a filepath
    * encrypted hash information (with both the hash value and the hash algorithm)
    * unencrypted hash information (with both the hash value and the hash algorithm)

    The hash algorithm we support are MD5 and SHA256, for the moment.
    '''

    filepath = data['filepath']
    LOG.info(f"Processing {filepath}")

    # Use user_id, and not elixir_id
    user_id = sanitize_user_id(data['elixir_id'])

    # Insert in database
    file_id = db.insert_file(filepath, user_id)

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
        encrypted_hash = data['encrypted_integrity']['hash']
        encrypted_algo = data['encrypted_integrity']['algorithm']
    except KeyError:
        LOG.info('Finding a companion file')
        encrypted_hash, encrypted_algo = checksum.get_from_companion(inbox_filepath)
        data['encrypted_integrity'] = {'hash': encrypted_hash,
                                       'algorithm': encrypted_algo }


    assert( isinstance(encrypted_hash,str) )
    assert( isinstance(encrypted_algo,str) )
    
    # Check integrity of encrypted file
    LOG.debug(f"Verifying the {encrypted_algo} checksum of encrypted file: {inbox_filepath}")
    if not checksum.is_valid(inbox_filepath, encrypted_hash, hashAlgo = encrypted_algo):
        LOG.error(f"Invalid {encrypted_algo} checksum for {inbox_filepath}")
        raise exceptions.Checksum(encrypted_algo, f'for {inbox_filepath}')
    LOG.debug(f'Valid {encrypted_algo} checksum for {inbox_filepath}')

    try:
        unencrypted_hash = data['unencrypted_integrity']['hash']
        unencrypted_algo = data['unencrypted_integrity']['algorithm']
    except KeyError:
        # Strip the suffix first.
        LOG.info('Finding a companion file')
        unencrypted_hash, unencrypted_algo = checksum.get_from_companion(inbox_filepath.with_suffix(''))
        data['unencrypted_integrity'] = {'hash': unencrypted_hash,
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
    cmd = CONF.get('ingestion','gpg_cmd',raw=True) % { 'file': str(inbox_filepath) }
    LOG.debug(f'GPG command: {cmd}\n')
    details, staging_checksum = crypto_ingest( cmd,
                                               str(inbox_filepath),
                                               unencrypted_hash,
                                               hash_algo = unencrypted_algo,
                                               active_key = active_master_key,
                                               master_key = master_pubkey,
                                               target = staging_filepath)
    db.set_encryption(file_id, details, staging_checksum)
    LOG.debug(f'Re-encryption completed')
    
    data['internal_data'] = {
        'file_id': file_id,
        'user_id': user_id,
        'filepath': str(staging_filepath),
    }
    LOG.debug(f"Reply message: {data}")
    return data

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
        LOG.debug('With SSL encryption')
        
    loop = asyncio.get_event_loop()
    try:
        LOG.info('Retrieving the Master Public Key')

        # Might raise exception
        active_master_key = loop.run_until_complete(_req(ACTIVE_MASTER_KEY, host, port, ssl=ssl_ctx, loop=loop))
        master_pubkey = loop.run_until_complete(_req(MASTER_PUBKEY, host, port, ssl=ssl_ctx, loop=loop))
        do_work = partial(work, active_master_key, master_pubkey.decode())
        
    except Exception as e:
        LOG.error(repr(e))
        LOG.critical('Problem contacting the Keyserver. Ingestion Worker terminated')
        loop.close()
        sys.exit(1)
    else:
        # upstream link configured in local broker
        consume(do_work, 'files', 'staged')
    finally:
        loop.close()

if __name__ == '__main__':
    main()
