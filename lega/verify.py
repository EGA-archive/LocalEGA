#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Re-Encryption Worker
#
####################################

It simply consumes message from the message queue configured in the [worker] section of the configuration files.

It defaults to the `tasks` queue.

It is possible to start several workers, of course!
However, they should have the gpg-agent socket location in their environment (when using GnuPG 2.0 or less).
In GnuPG 2.1, it is not necessary (Just point the `homedir` to the right place).

When a message is consumed, it must be of the form:
* filepath
* target
* hash (of the unencrypted content)
* hash_algo: the associated hash algorithm
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
    filename, org_hash, org_hash_algo, vault_filename, master_key = db.get_details(file_id)
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

    cega_connection = broker.get_connection('cega.broker')
    cega_channel = cega_connection.channel()

    lega_connection = broker.get_connection('local.broker')
    lega_channel = lega_connection.channel()
    lega_channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        broker.consume(lega_channel,
                       work,
                       from_queue  = CONF.get('local.broker','archived_queue'),
                       to_channel  = cega_channel,
                       to_exchange = CONF.get('cega.broker','exchange'),
                       to_routing  = CONF.get('cega.broker','routing_to'))
    except KeyboardInterrupt:
        lega_channel.stop_consuming()
    finally:
        lega_connection.close()
        cega_connection.close()

if __name__ == '__main__':
    main()
