#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module reads a message from the ``archived`` queue, and attempts to decrypt the file.

The decryption includes a checksum step.
It the checksum is valid, we consider that the archive has a properly
stored file. In such case, a message is sent to the local exchange
with the routing key: ``completed``.

.. note:: The header is not retrieved from the database, it is already in the message.
"""

import sys
import logging
from functools import partial
import hashlib

from crypt4gh.engine import decrypt

from .conf import CONF
from .utils import db, storage, key
from .utils.amqp import consume, get_connection

LOG = logging.getLogger(__name__)


class ChecksumFile():
    """Fake IO writer, accepting bytes to checksum but not writing them anywhere."""

    def __init__(self):
        """Initiliaze this IO writer for checksuming.

        The chosen checksum is `hashlib.sha256`.
        """
        self.md = hashlib.sha256()

    def write(self, data):
        """Send data to the checksum."""
        self.md.update(data)

    def hexdigest(self):
        """Get the checksum value in hex format."""
        return self.md.hexdigest()


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


@db.catch_error
@db.crypt4gh_to_user_errors
def work(key, mover, channel, data):
    """Verify that the file in the archive can be properly decrypted."""
    LOG.info('Verification | message: %s', data)

    file_id = data['file_id']
    header = bytes.fromhex(data['header'])
    archive_path = data['archive_path']
    LOG.info('Opening archive file: %s', archive_path)
    # If you can decrypt... the checksum is valid

    # Calculate the checksum of the original content
    cf = ChecksumFile()

    with mover.open(archive_path, 'rb') as infile:
        LOG.info('Decrypting')
        decrypt([(0, key.private(), None)],
                PrependHeaderFile(header, infile),
                cf)
        # decrypt will loop through the segments and send the output to the `cf` file handle.
        # The `cf` will only checksum the content (ie build the checksum of the unencrypted (original) file)
        # and never leave a trace on disk.

    digest = cf.hexdigest()
    LOG.info('Verification completed [sha256: %s]', digest)

    # Updating the database
    db.mark_completed(file_id)

    # Shape successful message
    org_msg = data['org_msg']
    org_msg.pop('file_id', None)
    org_msg['reference'] = file_id
    org_msg['decrypted_checksums'] = [{'value': digest_sha256, 'type': 'sha256'},
                                      {'value': digest_md5, 'type': 'md5'}]
    LOG.debug(f"Reply message: {org_msg}")
    return org_msg


def main(args=None):
    """Run verify service."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)  # re-conf

    store = getattr(storage, CONF.get_value('archive', 'storage_driver', default='FileStorage'))

    # Loading the key from its storage (be it from file, or from a remote location)
    # the key_config section in the config file should describe how
    # We don't use default values: bark if not supplied
    key_section = CONF.get_value('DEFAULT', 'master_key')
    key_loader = getattr(key, CONF.get_value(key_section, 'loader_class'))
    key_config = CONF[key_section]  # the whole section

    broker = get_connection('broker')
    do_work = partial(work, key_loader(key_config), store('archive', 'lega'), broker.channel())

    consume(do_work, broker, 'archived', 'completed')


if __name__ == '__main__':
    main()
