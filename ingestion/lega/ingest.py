#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Worker reading messages from the ``files`` queue, splitting the Crypt4GH header from the remainder of the file.

The header is stored in the database and the remainder is sent to the staging area.

It is possible to start several workers.

Upon completion, a message is sent to the local exchange with the routing key ``staged``.
"""

import logging
from functools import partial
import io
import os
import hashlib
import time

from crypt4gh.lib import body_decrypt, body_decrypt_parts
from crypt4gh.header import deconstruct, parse

from .conf import CONF
from .utils import exceptions, db, key, clean_message, name2fs, add_prefix, mkdirs
from .utils.amqp import consume, publish

LOG = logging.getLogger(__name__)


# This is the minimal implementation: read, readinto, and seek.
class VerifyPayloadFile():
    """IO reader to read a byte stream from a source file and tee-ing to:
    * copy the bytes to a destination file
    * checksum the stream
    * decrypt the stream
    """
    def __init__(self, fileobj, dstobj, md):
        """Initiliaze an IO reader with header prepended."""
        self.src = fileobj
        self.dst = dstobj
        self.md = md
        self.target_size = 0

    def seek(self, offset, whence):
        self.src.seek(offset, whence)

    def read(self, size=-1):
        if size < 1:  # Just in case...
            raise NotImplementedError(f'Reading {size} bytes: Unused case')
        data = self.src.read(size)
        self.md.update(data)
        self.dst.write(data)
        self.target_size += len(data)
        return data

    def readinto(self, b):
        assert(isinstance(b, bytearray))
        data = self.read(len(b))
        n = len(data)
        b[:n] = data
        return n

@db.check_canceled
def work(decryption_keys, inbox_fs, staging_fs, data):
    """Read a message, split the header and decrypt the remainder."""
    job_id = int(data['job_id'])
    LOG.info('Working on job id %s with data %s', job_id, data)

    filepath = data['filepath']
    username = data['user']

    LOG.info('Processing %s:%s', username, filepath)

    # Instantiate the inbox backend
    inbox_path = inbox_fs(username, filepath)
    
    # Check if file is in inbox
    if not os.path.exists(inbox_path):
        raise exceptions.NotFoundInInbox(inbox_path)  # return early

    # Ok, we have the file in the inbox
    # ---------------------------------

    LOG.debug('Opening %s', inbox_path)
    with open(inbox_path, 'rb') as infile:

        LOG.debug('Reading header')
        # Get session keys
        session_keys, edit_list = deconstruct(infile, decryption_keys)

        # Raise error we could not decrypt the header (ie no session keys retrieved)
        if not session_keys:
            raise exceptions.SessionKeyDecryptionError(header_hex)

        # Check if checksum of any of the session keys is in the record file
        sk_checksums = [hashlib.sha256(session_key).hexdigest().lower() for session_key in session_keys]
        LOG.debug('Session checksums: %s', sk_checksums)
        if db.has_session_keys_checksums(sk_checksums):
            raise exceptions.SessionKeyAlreadyUsedError(sk_checksums)

        # The infile is left right at the position of the payload
        pos = infile.tell()

        # Just record the header.
        infile.seek(0, io.SEEK_SET)  # rewind to beginning (it's ok: not a stream)
        header_bytes = infile.read(pos)
        header_hex = header_bytes.hex()
        data['header'] = header_hex

        # Making a staging area name
        staged_name = name2fs(f"{job_id:0>20}")  # filling with zeros, and 20 characters wide
        data['staged_name'] = staged_name
        staged_path = staging_fs(staged_name)
        data['staged_path'] = staged_path  # record for cleanup        
        mkdirs(staged_path) # Create parent directories

        # Verifying the payload and calculating the checksums of the original content
        LOG.debug('Verifying payload')
        md_sha256 = hashlib.sha256()
        md_md5 = hashlib.md5()  # we also calculate the md5 for the Accession ID attribution
                                # Note: it's useless, Make EBI drop md5 instead.

        LOG.info('Staging path: %s', staged_path)
        with open(staged_path, 'wb') as outfile:

            LOG.info('Decrypting / Copying / Checksuming the payload')
            md_payload = hashlib.sha256()

            def process_output():
                while True:
                    data = yield
                    md_md5.update(data)
                    md_sha256.update(data)

            output = process_output()
            next(output)  # start it

            # The virtual file/stream
            vfile = VerifyPayloadFile(infile, outfile, md_payload)

            try:
                # Decrypting chunk by chunk in memory. No trace on disk.
                start_time = time.time()
                if edit_list is None:
                    # No edit list: decrypt all segments from start to end
                    body_decrypt(vfile, session_keys, output, 0)
                else:
                    # Edit list: it drives which segments is decrypted
                    body_decrypt_parts(vfile, session_keys, output, edit_list=list(edit_list))
                    # Question: Should we raise an exception cuz we should not accept that type of files?
                LOG.debug('Elpased time: %.2f seconds', time.time() - start_time)
                data['target_size'] = vfile.target_size  # or os.stat ?
                payload_checksum = md_payload.hexdigest()
                data['payload_checksum'] = {'type': 'sha256', 'value': payload_checksum}
                LOG.info('Verification completed')
            #except ValueError as v:
            except Exception as v: # capture any error here
                raise exceptions.PayloadDecryptionError() from v

            # Add decrypted checksums to message
            decrypted_payload_checksum = md_sha256.hexdigest()
            data['decrypted_checksums'] = [{'type': 'sha256', 'value': decrypted_payload_checksum},
                                           {'type': 'md5', 'value': md_md5.hexdigest()}]  # for accession id

            # Record in DB
            db.mark_verified(job_id, data, decrypted_payload_checksum)

            # Record the session keys
            # Note: there is a data race here. We should 'check-then-insert' atomically.
            # So we let the database insertion happen and use the 'on-conflict clause', to raise an error
            db.insert_session_keys_checksums_sha256(job_id, sk_checksums)

    
    # Publish the answer
    clean_message(data)
    publish(data)
    # All good: Ack message


def main():

    # Loading the key from its storage (be it from file, or from a remote location)
    # the key_config section in the config file should describe how
    # We don't use default values: bark if not supplied
    key_section = CONF.get('DEFAULT', 'master_key')
    k = getattr(key, CONF.get(key_section, 'loader_class'))(key_section)
    decryption_keys = [(0, k.private(), None)]

    inbox_prefix = CONF.get('inbox', 'location', raw=True)
    def inbox_fs(user, path):
        return os.path.join(inbox_prefix % user, path.strip('/') )

    staging_prefix = CONF.get('staging', 'location', raw=True)
    def staging_fs(path):
        return os.path.join(staging_prefix, path.strip('/') )

    do_work = partial(work, decryption_keys, inbox_fs, staging_fs)

    # upstream link configured in local broker
    os.umask(0o077)  # no group nor world permissions
    consume(do_work)


# if __name__ == '__main__':
#     main()
