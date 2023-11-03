#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import hashlib
from functools import partial
import asyncio
from pathlib import Path
from hmac import compare_digest

from crypt4gh import header, lib as c4gh
import asyncpg

from . import clean_staging
from ..utils import exceptions

LOG = logging.getLogger(__name__)

CHUNKSIZE = 1024 * 1024

def name2fs(name):
    """Convert a name to a file system relative path."""
    return os.path.join(*list(name[i:i+3] for i in range(0, len(name), 3)))

async def checkum_and_compare(path, orgmd):
    LOG.debug('Reading again file %s', path)
    loop = asyncio.get_running_loop()
    md = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            # Making it asyncio
            do_read = partial(f.read, CHUNKSIZE)
            blob = await loop.run_in_executor(None, do_read) # default thread pool
            if not blob:
                break # We were at the end
            md.update(blob)

    c = md.hexdigest()
    
    if not compare_digest(c, orgmd): # could use c != orgmd
        LOG.error('Backup failed: different checksums for the payloads')
        LOG.error('* md1: %s', c)
        LOG.error('* md2: %s', orgmd)
        raise exceptions.ChecksumsNotMatching(path, c, orgmd)

async def send_completion(config, staging_path, message):
    # Success: Clean the staging path
    LOG.info('Cleaning staging path: %s', staging_path)
    clean_staging(config, message.parsed)
    
    # Publish the same message back
    await config.mq.cega_publish(message.parsed, 'files.completed', correlation_id=message.header.properties.content_type)


async def execute(config, message):

    data = message.parsed
    filepath = data['filepath']
    username = data['user']
    accession_id = data['accession_id']

    LOG.info('Processing %s: %s', username, filepath)

    staging_prefix = config.get('staging', 'location', raw=True)
    vault_prefix = config.get('vault', 'location')
    backup_prefix = config.get('backup', 'location')

    staging_path = os.path.join(staging_prefix % username, filepath.strip('/') )
    LOG.debug('Staging path: %s', staging_path)

    relative_path = name2fs(accession_id)
    vault_path = os.path.join(vault_prefix, relative_path)
    LOG.debug('Vault path: %s', vault_path)

    backup_path = os.path.join(backup_prefix, relative_path)
    LOG.debug('Backup path: %s', backup_path)

    # Create directories
    vpath = Path(vault_path)
    bpath = Path(backup_path)

    if vpath.exists(): # do nothing and return early
        LOG.info('Vault path already exists')
        return await send_completion(config, staging_path, message)

    vpath.parent.mkdir(parents=True, exist_ok=True)
    bpath.parent.mkdir(parents=True, exist_ok=True)

    # Checksuming the payload
    md_sha256 = hashlib.sha256()
    
    with open(staging_path, 'rb') as infile, open(vault_path, 'wb') as vfile, open(backup_path, 'wb') as bfile:

        LOG.debug('Reencrypting the header')
        try:
            service_key = (0, config.service_key.private(), None) # not checking the sender
            # Get session keys
            header_packets = header.parse(infile)
            decrypted_packets, _ = header.decrypt(header_packets, [service_key])  # don't bother with ignored packets
            if not decrypted_packets: # no packets were decrypted
                raise ValueError('No supported encryption method')

            data_packets, _ = header.partition_packets(decrypted_packets)

            # if edit_packet:
            #     raise exceptions.FromUser('Support for Crypt4GH edit list has been removed')

        except Exception as e:
            LOG.error('Decryption error: %r', e)
            raise exceptions.Crypt4GHHeaderDecryptionError() from e


        # The master key.
        # Note: we do not use an ephemeral key: the service key is the sender
        master_key = (0, service_key[1], config.master_pubkey)

        # The infile is left right at the position of the payload
        # Decrypt and re-encrypt the header
        master_packets = [encrypted_packet for packet in decrypted_packets
                          for encrypted_packet in header.encrypt(packet, [master_key])]
        master_header = header.serialize(master_packets)

        LOG.info('Copying / Checksuming the payload')
        loop = asyncio.get_running_loop()
        while True:
            # Making it asyncio
            do_read = partial(infile.read, CHUNKSIZE)
            blob = await loop.run_in_executor(None, do_read) # default thread pool
            #blob = infile.read(CHUNKSIZE)
            
            if not blob:
                break # We were at the end
            
            md_sha256.update(blob)

            # Copy the chunk
            # Note: we should use shutil.copyfile (which uses fastcopy or sendfile)
            do_write = partial(vfile.write, blob)
            await loop.run_in_executor(None, do_write)
            do_write = partial(bfile.write, blob)
            await loop.run_in_executor(None, do_write)

    # Read the encrypted payload checksum
    payload_sha256_checksum = md_sha256.hexdigest()

    # Flush the file system and its cache here?
    # os.fsync()

    # We now read the Vault file again
    await checkum_and_compare(vault_path, payload_sha256_checksum)
    # Same for the backup file
    await checkum_and_compare(backup_path, payload_sha256_checksum)

    # encrypted payload size
    encrypted_filesize = os.path.getsize(vault_path)

    # We read the decrypted_checksum from the message, we don't compute it at this stage
    decrypted_sha256_checksum = data.get('decrypted_checksums', [{}])[0].get('value')

    # Save to database
    LOG.debug('Saving to database')
    await config.db.save_file(filepath,
                              encrypted_filesize,
                              master_header,
                              payload_sha256_checksum,
                              decrypted_sha256_checksum,
                              accession_id,
                              relative_path)

    # All good: send completion
    return await send_completion(config, staging_path, message)

