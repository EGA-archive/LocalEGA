#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Verifying the vault files

This module reads a message from the ``staged`` queue, decrypts the
files and recalculates its checksum.

It the checksum matches the corresponding information in the file,
we consider that the vault has a properly stored file.

Upon completion, a message is sent to the local exchange with the
routing key: ``completed``.

'''

import sys
import os
import logging
from functools import partial
from urllib.request import urlopen

from legacryptor.crypt4gh import get_key_id, header_to_records, body_decrypt

from .conf import CONF
from .utils import db, exceptions, storage
from .utils.amqp import consume

LOG = logging.getLogger(__name__)

def get_records(header):
    keyid = get_key_id(header)
    LOG.info(f'Key ID {keyid}')
    keyurl = CONF.get('quality_control', 'keyserver_endpoint', raw=True) % keyid
    LOG.info(f'Retrieving the Private Key from {keyurl}')
    with urlopen(keyurl) as response:
        privkey = response.read()
        return header_to_records(privkey, header, os.environ['LEGA_PASSWORD'])

@db.catch_error
def work(mover, data):
    '''Verifying that the file in the vault does decrypt properly'''

    LOG.debug(f'Verifying message: {data}')

    file_id = data.pop('internal_data') # can raise KeyError
    _, vault_path, stable_id, header = db.get_info(file_id)

    # Get it from the header and the keyserver
    records = get_records(bytes.fromhex(header)) # might raise exception
    r = records[0] # only first one

    # LOG.info(f'Session Key: {r.session_key.hex()}')
    # LOG.info(f'         IV: {r.iv.hex()}')
    
    LOG.debug('Opening vault file: %s', vault_path)
    # If you can decrypt... the checksum is valid
    with mover.open(vault_path, 'rb') as infile:
        body_decrypt(r, infile) # It will ignore the output

    db.set_status(file_id, db.Status.Completed)
    data['status'] = { 'state': 'COMPLETED', 'details': stable_id }
    LOG.debug(f"Reply message: {data}")
    return data

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    store = getattr(storage, CONF.get('vault', 'driver', fallback='FileStorage'))
    do_work = partial(work, store())

    consume(do_work, 'staged', 'completed')

if __name__ == '__main__':
    main()
