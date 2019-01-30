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
import os
import logging
from functools import partial
from urllib.request import urlopen
from urllib.error import HTTPError
import hashlib

from legacryptor.crypt4gh import get_key_id, header_to_records, body_decrypt

from .conf import CONF
from .utils import db, exceptions, storage
from .utils.amqp import consume, get_connection

LOG = logging.getLogger(__name__)


def get_records(header):
    """Retrieve Crypt4GH header information (records) from Keyserver."""
    keyid = get_key_id(header)
    LOG.info(f'Key ID {keyid}')
    keyurl = CONF.get_value('quality_control', 'keyserver_endpoint', raw=True) % keyid
    verify = CONF.get_value('quality_control', 'verify_certificate', conv=bool)
    LOG.info(f'Retrieving the Private Key from {keyurl} (verify certificate: {verify})')

    if verify:
        ctx = None  # nothing to be done: done by default in urlopen
    else:  # no verification
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        with urlopen(keyurl, context=ctx) as response:
            assert(response.status == 200)
            privkey = response.read()
            if not privkey:  # Correcting a bug in the EGA keyserver
                # When key not found, it returns a 200 and an empty payload.
                # It should probably be changed to a 404
                raise exceptions.PGPKeyError('No PGP key found')
            return header_to_records(privkey, header, os.environ['LEGA_PASSWORD']), keyid
    except HTTPError as e:
        LOG.error(e)
        msg = str(e)
        if e.code == 404:  # If key not found, then probably wrong key.
            raise exceptions.PGPKeyError(msg)
        # Otherwise
        raise exceptions.KeyserverError(msg)
    # except Exception as e:
    #     raise exceptions.KeyserverError(str(e))


@db.catch_error
@db.crypt4gh_to_user_errors
def work(chunk_size, mover, channel, data):
    """Verify that the file in the archive can be properly decrypted."""
    LOG.info('Verification | message: %s', data)

    file_id = data['file_id']
    header = bytes.fromhex(data['header'])[16:]  # in hex -> bytes, and take away 16 bytes
    archive_path = data['archive_path']

    # Get it from the header and the keyserver
    records, key_id = get_records(header)  # might raise exception
    r = records[0]  # only first one

    LOG.info('Opening archive file: %s', archive_path)
    # If you can decrypt... the checksum is valid

    # Calculate the checksum of the original content
    md = hashlib.sha256()

    def checksum_content(data):
        md.update(data)

    with mover.open(archive_path, 'rb') as infile:
        LOG.info('Decrypting (chunk size: %s)', chunk_size)
        body_decrypt(r, infile, process_output=checksum_content, chunk_size=chunk_size)

    digest = md.hexdigest()
    LOG.info('Verification completed [sha256: %s]', digest)

    # Updating the database
    db.mark_completed(file_id)

    # Shape successful message
    org_msg = data['org_msg']
    org_msg.pop('file_id', None)
    org_msg['reference'] = file_id
    org_msg['checksum'] = {'value': digest, 'algorithm': 'sha256'}
    LOG.debug(f"Reply message: {org_msg}")
    return org_msg


def main(args=None):
    """Run verify service."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)  # re-conf

    store = getattr(storage, CONF.get_value('archive', 'storage_driver', default='FileStorage'))
    chunk_size = CONF.get_value('archive', 'chunk_size', conv=int, default=1 << 22)  # 4 MB

    broker = get_connection('broker')
    do_work = partial(work, chunk_size, store('archive', 'lega'), broker.channel())

    consume(do_work, broker, 'archived', 'completed')


if __name__ == '__main__':
    main()
