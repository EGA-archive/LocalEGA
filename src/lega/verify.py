#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Verifying the vault files
#
####################################

This module checks the files in the vault, by decrypting them and
recalculating their checksum.
It the checksum still corresponds to the one of the original file,
we consider that the vault has properly stored the file.
'''

import sys
import logging
import os

from .conf import CONF
from .utils import crypto, db, checksum
from .utils import db_log_error_on_files, checksum
from .utils.amqp import get_connection, consume

LOG = logging.getLogger('verify')

@db_log_error_on_files
def work(data):
    '''Verifying that the file in the vault does decrypt properly'''

    file_id = data['file_id']
    filename, org_hash, org_hash_algo, vault_filename, vault_checksum = db.get_details(file_id)

    if not checksum.is_valid(vault_filename, vault_checksum, hashAlgo='sha256'):
        raise VaultDecryption(vault_filename)

    return { 'vault_name': vault_filename, 'org_name': filename }
    
def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    from_broker = (get_connection('local.broker'), 'archived')
    to_broker = (get_connection('cega.broker'), CONF.get('cega.broker','exchange'), CONF.get('cega.broker','file_routing'))
    consume(from_broker, work, to_broker)

if __name__ == '__main__':
    main()
