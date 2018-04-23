#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Verifying the vault files

This module reads a message from the ``archived`` queue and
recalculates the checksum of the requested vault file.

It the checksum matches the corresponding information in the database,
we consider that the vault has properly stored the file.

Upon completion, a message is sent to the local exchange with the
routing key: ``completed``.
'''

import sys
import logging

from .conf import CONF
from .utils import checksum, db, exceptions
from .utils.amqp import consume

LOG = logging.getLogger('verify')

@db.catch_error
def work(data):
    '''Verifying that the file in the vault does decrypt properly'''

    LOG.debug(f'Verifying message: {data}')

    file_id = data.pop('internal_data') # can raise KeyError
    filename, _, org_hash_algo, vault_filename, stable_id, vault_checksum = db.get_details(file_id)

    if not checksum.is_valid(vault_filename, vault_checksum, hashAlgo='sha256'):
        raise exceptions.VaultDecryption(vault_filename)

    data['status'] = { 'state': 'COMPLETED', 'details': stable_id }
    return data

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    consume(work, 'archived', 'completed')

if __name__ == '__main__':
    main()
