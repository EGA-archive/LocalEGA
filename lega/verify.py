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
import logging

from legacryptor.crypt4gh import get_key_id

from .conf import CONF
from .utils import db, exceptions
from .utils.amqp import consume

LOG = logging.getLogger(__name__)

def get_priv_key(header):
    try:
        keyid = get_key_id(header)
        LOG.info(f'Key ID {keyid}')
        keyurl = CONF.get_value('quality_control', 'keyserver_endpoint', raw=True) % keyid
        LOG.info(f'Retrieving the Master Public Key from {keyurl}')
        with urlopen(keyurl) as response:
            return response.read()
    except Exception as e:
        LOG.error(repr(e))
        LOG.critical('Problem contacting the Keyserver. Terminating...')
        sys.exit(1)

@db.catch_error
def work(data):
    '''Verifying that the file in the vault does decrypt properly'''

    LOG.debug(f'Verifying message: {data}')

    file_id = data.pop('internal_data') # can raise KeyError
    _, vault_path, stable_id, header = db.get_info(file_id)

    # Get it from the header and the keyserver
    privkey = get_priv_key(header)

    # If you can decrypt... the checksum is valid
    with open(vault_path, 'rb') as infile:
        decrypt(privkey, infile) # It will ignore the output

    db.set_status(file_id, 'Completed')
    data['status'] = { 'state': 'COMPLETED', 'details': stable_id }
    LOG.debug(f"Reply message: {data}")
    return data

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    consume(work, 'staged', 'completed')

if __name__ == '__main__':
    main()
