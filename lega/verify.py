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
    LOG.info('Retrieving the Private Key from %s', keyurl)

    context = None
    if keyurl.startswith('https'):
        import ssl

        LOG.debug("Enforcing a TLS context")
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)  # Enforcing (highest) TLS version (so... 1.2?)

        context.verify_mode = ssl.CERT_NONE
        # Require server verification
        if CONF.get_value('quality_control', 'verify_peer', conv=bool, default=False):
            LOG.debug("Require server verification")
            context.verify_mode = ssl.CERT_REQUIRED
            cacertfile = CONF.get_value('quality_control', 'cacertfile', default=None)
            if cacertfile:
                context.load_verify_locations(cafile=cacertfile)

        # Check the server's hostname
        server_hostname = CONF.get_value('quality_control', 'server_hostname', default=None)
        verify_hostname = CONF.get_value('quality_control', 'verify_hostname', conv=bool, default=False)
        if verify_hostname:
            LOG.debug("Require hostname verification")
            assert server_hostname, "server_hostname must be set if verify_hostname is"
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

        # If client verification is required
        certfile = CONF.get_value('quality_control', 'certfile', default=None)
        if certfile:
            LOG.debug("Prepare for client verification")
            keyfile = CONF.get_value('quality_control', 'keyfile')
            context.load_cert_chain(certfile, keyfile=keyfile)

    try:
        with urlopen(keyurl, context=context) as response:
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
    # key id is not used thus not using it (2nd argument below)
    records, _ = get_records(header)  # might raise exception
    r = records[0]  # only first one

    LOG.info('Opening archive file: %s', archive_path)
    # If you can decrypt... the checksum is valid

    # Calculate the checksum of the original content
    sha256_checksum = hashlib.sha256()
    md5_checksum = hashlib.md5()

    def checksum_content(data):
        sha256_checksum.update(data)
        md5_checksum.update(data)

    with mover.open(archive_path, 'rb') as infile:
        LOG.info('Decrypting (chunk size: %s)', chunk_size)
        body_decrypt(r, infile, process_output=checksum_content, chunk_size=chunk_size)

    digest_md5 = md5_checksum.hexdigest()
    digest_sha256 = sha256_checksum.hexdigest()
    LOG.info('Verification completed [md5: %s]', digest_md5)
    LOG.info('Verification completed [sha256: %s]', digest_sha256)

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
    chunk_size = CONF.get_value('archive', 's3_chunk_size', conv=int, default=1 << 22)  # 4 MB

    broker = get_connection('broker')
    do_work = partial(work, chunk_size, store('archive', 'lega'), broker.channel())

    consume(do_work, broker, 'archived', 'completed')


if __name__ == '__main__':
    main()
