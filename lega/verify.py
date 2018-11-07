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
import hashlib
import io

from nacl.public import PrivateKey
from nacl.encoding import HexEncoder as KeyFormatter
#from nacl.encoding import URLSafeBase64Encoder as KeyFormatter
from crypt4gh.crypt4gh import Header, body_decrypt

from .conf import CONF, configure
from .utils import db, exceptions, storage, errors
from .utils.amqp import consume, publish

LOG = logging.getLogger(__name__)

@errors.catch(ret_on_error=(None,True))
def _work(mover, correlation_id, data):
    '''Verifying that the file in the vault can be properly decrypted.'''

    LOG.info('[%s] Verification | message: %s', correlation_id, data)

    file_id = data['file_id']

    if db.is_disabled(file_id):
        LOG.info('[%s] Operation canceled because database entry marked as DISABLED (for file_id %s)', correlation_id, file_id)
        return None, False # do nothing

    header = bytes.fromhex(data['header']) # in hex -> bytes
    vault_path = data['vault_path']

    # Load the LocalEGA private key
    key_location = CONF.get_value('DEFAULT', 'private_key')
    LOG.info('[%s] Retrieving the Private Key from %s', correlation_id, key_location)
    with open(key_location, 'rb') as k:
        privkey = PrivateKey(k.read(), KeyFormatter)

    LOG.info('[%s] Opening vault file: %s', correlation_id, vault_path)
    # If you can decrypt... the checksum is valid

    header = Header.from_stream(io.BytesIO(header))
    checksum, session_key, nonce, method = header.decrypt(privkey)

    # Calculate checksum of the session key
    skmd = hashlib.sha256()
    skmd.update(session_key)
    sk_checksum = skmd.hexdigest().lower()
    if db.check_session_key_checksum(sk_checksum, 'sha256'):
        raise exceptions.SessionKeyAlreadyUsedError(sk_checksum)

    # If you can decrypt, the file is properly sha256-checksumed
    md = hashlib.md5() # we also calculate the md5 for the stable ID attribution
    with mover.open(vault_path, 'rb') as infile:
        body_decrypt(checksum, session_key, nonce, infile, process_output=md.update)
        
    # Convert to hex
    checksum = checksum.hex()
    LOG.info('[%s] Verification completed [sha256: %s]', correlation_id, checksum)
    md5_digest = md.hexdigest()
    LOG.info('[%s] Verification completed [md5: %s]', correlation_id, md5_digest)

    # Updating the database
    db.update(file_id, { 'status': 'COMPLETED',
                         'unencrypted_checksum': checksum,
                         'unencrypted_checksum_type':'SHA256',
                         'session_key_checksum': sk_checksum,
                         'session_key_checksum_type':'SHA256'})

    # Send to QC
    data.pop('status', None)
    LOG.debug('[%s] Sending message to QC: ',correlation_id, data)
    publish(data, 'lega', 'qc', correlation_id=correlation_id) # We keep the org msg in there

    # Shape successful message
    org_msg = data['org_msg']
    org_msg.pop('file_id', None)
    org_msg['decrypted_checksums'] = [{ 'type': 'sha256', 'value': checksum },
                                      { 'type': 'md5', 'value': md5_digest }] # for stable id
    LOG.debug("[%s] Reply message: %s", correlation_id, org_msg)
    return (org_msg, False)

@configure
def main():

    fs = getattr(storage, CONF.get_value('vault', 'driver', default='FileStorage'))
    do_work = partial(_work, fs())

    consume(do_work, 'archived', 'completed')

if __name__ == '__main__':
    main()
