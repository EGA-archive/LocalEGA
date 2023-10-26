#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import io
import os
import hashlib
import time
from functools import partial
import asyncio
from pathlib import Path

from crypt4gh import header, lib as c4gh
import asyncpg

from . import clean_staging
from ..utils import exceptions

LOG = logging.getLogger(__name__)

def clean_staging_on_failure(func):    
    async def wrapper(config, message):
        try:
            return await func(config, message)
        except exceptions.AlreadyInProgress as e:
            LOG.warning('Ignoring: %r', e)
            # raise e
        except Exception as e:
            LOG.error('Cleaning staging on error: %s', e)
            clean_staging(config, message.parsed)
            raise e
    return wrapper

@clean_staging_on_failure
async def execute(config, message):

    data = message.parsed
    filepath = data['filepath']
    username = data['user']

    LOG.info('Processing %s: %s', username, filepath)

    inbox_prefix = config.get('inbox', 'location', raw=True)
    staging_prefix = config.get('staging', 'location', raw=True)
    
    inbox_path = os.path.join(inbox_prefix % username, filepath.strip('/') )
    LOG.debug('Inbox path %s', inbox_path)
    staging_path = os.path.join(staging_prefix % username, filepath.strip('/') )
    LOG.debug('Staging path: %s', staging_path)
    
    if not os.path.exists(inbox_path):
        raise exceptions.NotFoundInInbox(filepath)  # return early

    # Check if we have the file in the staging area,
    # and also if we should cancel it, cuz we already have a staging file.
    #
    # That means, another handler has picked up another message regarding that inbox file
    # and there was no cancel in between the 2 messages.
    #
    # We are aware that there is a data race (in between the if-check and the action)
    # but it'll work find in most cases.
    # Note: this is not about asyncio, this is about starting another handler/listener concurrently.
    #       The broker queue will handle not giving the same message to those concurrent handlers
    #       but if the message is delivered twice, those concurrent handlers will compete for the staging filepath
    #
    # Maybe fcntl.flock(fd, fcntl.LOCK_EX) can be used.
    #
    if os.path.exists(staging_path):
        raise exceptions.AlreadyInProgress(filepath)  # return early

    Path(staging_path).parent.mkdir(parents=True, exist_ok=True)
    # possible data race here:
    # another ingestion might be in the step of cleaning up and would delete this directory tree

    with open(staging_path, 'wb') as outfile, open(inbox_path, 'rb') as infile: # and truncate stage file

        LOG.debug('Reading header')
        try:
            service_key = (0, config.service_key.private(), None) # not checking the sender
            # Get session keys
            session_keys, edit_list = header.deconstruct(infile, [service_key])
        except Exception as e:
            LOG.error('Decryption error: %r', e)
            raise exceptions.Crypt4GHHeaderDecryptionError() from e

        # Raise error we could not decrypt the header (ie no session keys retrieved)
        if not session_keys:
            raise exceptions.SessionKeyDecryptionError('No session keys found')

        if edit_list:
            raise exceptions.FromUser('Support for Crypt4GH edit list has been removed')

           
        # The infile is left right at the position of the payload
        pos = infile.tell()

        # Just record the header.
        infile.seek(0, io.SEEK_SET)  # rewind to beginning (it's ok: not a stream)
        header_bytes = infile.read(pos)
        outfile.write(header_bytes)

        # Verifying the payload and calculating the checksums of the original content
        LOG.debug('Verifying payload')
        md_sha256 = hashlib.sha256()

        LOG.info('Decrypting / Copying / Checksuming the payload')
        loop = asyncio.get_running_loop()
        try:
            # Decrypting chunk by chunk in memory. No trace on disk.
            start_time = time.time()
            while True:
                # Making it asyncio
                do_read = partial(infile.read, c4gh.CIPHER_SEGMENT_SIZE)
                ciphersegment = await loop.run_in_executor(None, do_read) # default thread pool
                #ciphersegment = infile.read(c4gh.CIPHER_SEGMENT_SIZE)

                ciphersegment_len = len(ciphersegment)
                if ciphersegment_len == 0:
                    break # We were at the last segment. Exits the loop
                assert( ciphersegment_len > c4gh.CIPHER_DIFF )

                # Copy the chunk
                do_write = partial(outfile.write, ciphersegment)
                await loop.run_in_executor(None, do_write) # default thread pool
                # outfile.write(ciphersegment)

                # Decrypt the segment
                segment = c4gh.decrypt_block(ciphersegment, session_keys)
                md_sha256.update(segment)

            LOG.debug('Elpased time: %.2f seconds', time.time() - start_time)
            LOG.info('Verification completed')

        except Exception as v: # capture any error here
            raise exceptions.Crypt4GHPayloadDecryptionError() from v

        # Add decrypted checksums to message
        decrypted_payload_checksum = md_sha256.hexdigest()
        data['decrypted_checksums'] = [{'type': 'sha256', 'value': decrypted_payload_checksum}] # for accession id

        # Publish the verified message
        await config.mq.cega_publish(data, 'files.verified', correlation_id=message.header.properties.content_type)
