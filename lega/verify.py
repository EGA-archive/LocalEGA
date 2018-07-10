#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''This module reads a message from the ``archived`` queue, and
attempts to decrypt the file. The decryption includes a checksum step.
It the checksum is valid, we consider that the vault has a properly
stored file. In such case, a message is sent to the local exchange
with the routing key: ``completed``.

Note: The header is not retrieved from the database, it is already in the message.
'''

import sys
import os
import logging
from functools import partial
from urllib.request import urlopen
from urllib.error import HTTPError

from legacryptor.crypt4gh import get_key_id, header_to_records, body_decrypt

from .conf import CONF
from .utils import db, exceptions, storage
from .utils.amqp import consume, publish, get_connection

LOG = logging.getLogger(__name__)

def get_records(header):
    keyid = get_key_id(header)
    LOG.info(f'Key ID {keyid}')
    keyurl = CONF.get_value('quality_control', 'keyserver_endpoint', raw=True) % keyid
    verify = CONF.get_value('quality_control', 'verify_certificate', conv=bool)
    LOG.info(f'Retrieving the Private Key from {keyurl} (verify certificate: {verify})')

    if verify:
        ctx=None # nothing to be done: done by default in urlopen
    else: # no verification
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
        if e.code == 404: # If key not found, then probably wrong key.
            raise exceptions.PGPKeyError(msg)
        # Otherwise
        raise exceptions.KeyserverError(msg)
    except Exception as e:
        raise exceptions.KeyserverError(str(e))

@db.catch_error
@db.crypt4gh_to_user_errors
def work(chunk_size, mover, channel, data):
    '''Verifying that the file in the vault can be properly decrypted.'''

    LOG.info('Verification | message: %s', data)

    file_id = data['file_id']
    header = bytes.fromhex(data['header'])[16:] # in hex -> bytes, and take away 16 bytes
    vault_path = data['vault_path']
    stable_id = data['stable_id']

    # Get it from the header and the keyserver
    records, key_id = get_records(header) # might raise exception
    r = records[0] # only first one

    LOG.info('Opening vault file: %s', vault_path)
    # If you can decrypt... the checksum is valid
    with mover.open(vault_path, 'rb') as infile:
        LOG.info('Decrypting (chunk size: %s)', chunk_size)
        body_decrypt(r, infile, chunk_size=chunk_size) # It will ignore the output

    LOG.info('Verification completed. Updating database.')
    db.set_status(file_id, db.Status.Completed)

    # Send to QC
    data.pop('status', None)
    data['key_id'] = key_id
    LOG.debug(f'Sending message to QC: {data}')
    publish(data, channel, 'lega', 'qc') # We keep the org msg in there

    org_msg = data['org_msg']
    org_msg['status'] = { 'state': 'COMPLETED', 'details': stable_id }
    LOG.debug(f"Reply message: {org_msg}")
    return org_msg

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    store = getattr(storage, CONF.get_value('vault', 'driver', default='FileStorage'))
    chunk_size = CONF.get_value('vault', 'chunk_size', conv=int, default=1<<22) # 4 MB

    broker = get_connection('broker')
    do_work = partial(work, chunk_size, store(), broker.channel())

    consume(do_work, broker, 'archived', 'completed')

if __name__ == '__main__':
    main()
