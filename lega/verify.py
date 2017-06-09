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
from . import crypto
from . import amqp as broker
from . import db
from .utils import check_error, checksum

LOG = logging.getLogger('verify')

@check_error
def work(data):
    '''Verifying that the file in the vault does decrypt properly'''

    file_id = data['file_id']
    filename, org_hash, org_hash_algo, vault_filename, vault_checksum = db.get_details(file_id)

    #crypto.decrypt_from_vault( vault_filename, org_hash, org_hash_algo )
    # raise exception if fail
    if not checksum(vault_filename, vault_checksum, hashAlgo='sha256'):
        raise VaultDecryption(vault_filename)

    return { 'vault_name': vault_filename, 'org_name': filename }
    
def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    connection = broker.get_connection('local.broker')
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        broker.consume(channel,
                       work,
                       from_queue  = CONF.get('local.broker','archived_queue'),
                       to_channel  = channel,
                       to_exchange = CONF.get('local.broker','exchange'),
                       to_routing  = CONF.get('local.broker','routing_verified'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
