#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module reads a message from the ``archived`` queue, and attempts to decrypt the file.

The decryption includes a checksum step.
It the checksum is valid, we consider that the vault has a properly
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

from .utils import db, exceptions, storage, context
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
            privkey = response.read()
            return header_to_records(privkey, header, os.environ['LEGA_PASSWORD']), keyid
    except HTTPError as e:
        LOG.error(e)
        msg = str(e)
        if e.code == 404:  # If key not found, then probably wrong key.
            raise exceptions.PGPKeyError(msg)
        # Otherwise
        raise exceptions.KeyserverError(msg)
    except Exception as e:
        raise exceptions.KeyserverError(str(e))


@db.catch_error
@db.crypt4gh_to_user_errors
def work(chunk_size, mover, channel, ctx, data):
    """Verify that the file in the vault can be properly decrypted."""
    LOG.info('Verification | message: %s', data)

    file_id = data['file_id']
    header = bytes.fromhex(data['header'])[16:]  # in hex -> bytes, and take away 16 bytes
    vault_path = data['vault_path']

    # Get it from the header and the keyserver
    records, key_id = get_records(header)  # might raise exception
    r = records[0]  # only first one

    LOG.info('Opening vault file: %s', vault_path)
    # If you can decrypt... the checksum is valid

    # Calculate the checksum of the original content
    md = hashlib.sha256()

    def checksum_content(data):
        md.update(data)

    with mover.open(vault_path, 'rb') as infile:
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

    ctx = context.Context()
    ctx.setup(args)  # re-conf

    store = getattr(storage, ctx.conf.get_value('vault', 'driver', default='FileStorage'))
    chunk_size = ctx.conf.get_value('vault', 'chunk_size', conv=int, default=1 << 22)  # 4 MB

    broker = get_connection('broker', ctx.conf)
    do_work = partial(work, chunk_size, store(ctx.conf), broker.channel())

    consume(do_work, ctx, broker, 'archived', 'completed')


if __name__ == '__main__':
    main()
