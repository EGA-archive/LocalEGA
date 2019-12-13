#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module reads a message from the ``archived`` queue, and attempts to decrypt the file.

The decryption includes a checksum step.
It the checksum is valid, we consider that the archive has a properly
stored file. In such case, a message is sent to the local exchange
with the routing key: ``completed``.

.. note:: The header is not retrieved from the database, it is already in the message.
"""

import logging
from functools import partial
import hashlib
import time
from io import BytesIO

from crypt4gh.lib import body_decrypt, body_decrypt_parts
from crypt4gh.header import deconstruct

from .conf import CONF, configure
from .utils import db, storage, key, errors, exceptions
from .utils.amqp import consume

LOG = logging.getLogger(__name__)


class PrependHeaderFile():
    """IO reader to inject header bytes in front of file."""

    def __init__(self, header, bulk):
        """Initiliaze an IO reader with header prepended."""
        assert(header)
        self.header = header
        self.file = bulk
        self.pos = 0
        self.header_length = len(header)

    def seek(self, offset, whence):
        """Seek within the file."""
        # Not needed because we decrypt all of it, and not only a range
        raise NotImplementedError(f'Moving file pointer to {offset}: Unused case')

    def read(self, size=-1):
        """Read `size` bytes.

        If size<-1, raise NotImplementedError, because it is an unused case.
        """
        # if size < 0: # read all
        #     if self.pos >= self.length: # heade consumed already
        #         return self.file.read()
        #     return self.header[self.pos:] + self.file.read()
        if size < 1:
            raise NotImplementedError(f'Reading {size} bytes: Unused case')

        if self.pos + size <= self.header_length:
            res = self.header[self.pos:self.pos+size]
            self.pos += size
            return res

        if self.pos + size > self.header_length:
            if self.pos >= self.header_length:  # already
                return self.file.read(size)

            assert(self.header_length - self.pos > 0)
            res = self.header[self.pos:]
            self.pos += size
            return res + self.file.read(size-(self.header_length - self.pos))

    def readinto(self, b):
        """Fill the buffer `b`.

        Returns the number of bytes read.
        """
        assert(isinstance(b, bytearray))
        data = self.read(len(b))
        n = len(data)
        b[:n] = data
        return n

    # def readinto(self, b):
    #     m = memoryview(b).cast('B')
    #     data = self.read(len(m))
    #     n = len(data)
    #     m[:n] = data
    #     return n


@errors.catch(ret_on_error=(None, True))
def work(key, mover, data):
    """Verify that the file in the archive can be properly decrypted."""
    LOG.info('Verification | message: %s', data)

    file_id = data['file_id']
    header = bytes.fromhex(data['header'])
    archive_path = data['archive_path']
    LOG.info('Opening archive file: %s', archive_path)
    # If you can decrypt... the checksum is valid

    decryption_keys = [(0, key.private(), None)]

    # Calculate checksum of the session key
    # That requires
    session_keys, edit_list = deconstruct(BytesIO(header), decryption_keys)

    if not session_keys:
        raise exceptions.SessionKeyDecryptionError(header)

    sk_checksums = [hashlib.sha256(session_key).hexdigest().lower() for session_key in session_keys]
    if db.check_session_keys_checksums(sk_checksums):
        raise exceptions.SessionKeyAlreadyUsedError(sk_checksums)

    # Calculate the checksum of the original content
    md_sha256 = hashlib.sha256()
    md_md5 = hashlib.md5()  # we also calculate the md5 for the stable ID attribution (useless: Make EBI drop md5).

    def process_output():
        while True:
            data = yield
            md_md5.update(data)
            md_sha256.update(data)
    output = process_output()
    next(output)  # start it

    start_time = time.time()

    # Decrypting chunk by chunk in memory.
    # No trace on disk.
    with mover.open(archive_path, 'rb') as infile:
        LOG.info('Decrypting')
        if edit_list is None:
            # No edit list: decrypt all segments from start to end
            body_decrypt(infile, session_keys, output, 0)
        else:
            # Edit list: it drives which segments is decrypted
            body_decrypt_parts(infile, session_keys, output, edit_list=list(edit_list))
            # Question: Should we raise an exception cuz we should not accept that type of files?

    LOG.debug('Elpased time: %.2f seconds', time.time() - start_time)

    digest_sha256 = md_sha256.hexdigest()
    LOG.info('Verification completed [sha256: %s]', digest_sha256)
    digest_md5 = md_md5.hexdigest()
    LOG.info('Verification completed [md5: %s]', digest_md5)

    # Updating the database
    db.mark_completed(file_id, sk_checksums, digest_sha256)  # sha256 only

    # Shape successful message
    org_msg = data['org_msg']
    org_msg.pop('file_id', None)
    org_msg['decrypted_checksums'] = [{'type': 'sha256', 'value': digest_sha256},
                                      {'type': 'md5', 'value': digest_md5}]  # for stable id
    # org_msg['reference'] = file_id
    LOG.debug(f"Reply message: {org_msg}")
    return (org_msg, False)


@configure
def main():
    """Run verify service."""
    store = getattr(storage, CONF.get_value('archive', 'storage_driver', default='FileStorage'))

    # Loading the key from its storage (be it from file, or from a remote location)
    # the key_config section in the config file should describe how
    # We don't use default values: bark if not supplied
    key_section = CONF.get_value('DEFAULT', 'master_key')
    key_loader = getattr(key, CONF.get_value(key_section, 'loader_class'))
    key_config = CONF[key_section]  # the whole section

    do_work = partial(work, key_loader(key_config), store('archive', 'lega'))

    consume(do_work, 'archived', 'completed')


if __name__ == '__main__':
    main()
