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

LOG = logging.getLogger('verify')

def work(data):
    '''Verifying that the file in the vault does decrypt properly'''

    file_id = data['file_id']
    filename, org_hash, org_hash_algo, vault_filename = db.get_details(file_id)
    staging_folder = data['staging_folder']

    try:
        
        crypto.decrypt_from_vault( vault_filename, org_hash, org_hash_algo )
        # raise exception if fail

        # Clean the staging area: remove parent folder if empty
        try:
            os.rmdir(staging_folder) # raise exception is not empty
            LOG.debug(f'Removing {staging_folder}')
        except OSError:
            pass

        return {
            'vault_name': vault_filename,
            'org_name': filename
        }
    except Exception as e:
        if isinstance(e,AssertionError):
            raise e
        errmsg = f'{e.__class__.__name__}: {e!s}'
        LOG.error(errmsg)
        db.set_error(file_id, e)
        
    
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
