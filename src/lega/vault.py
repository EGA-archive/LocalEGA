#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Listener moving files to the Vault
#
####################################

It simply consumes message from the message queue configured in the [vault] section.

It defaults to the `completed` queue.

When a message is consumed, it must at least contain:
* file_id
* filepath
* user_id
'''

import sys
import logging
import json
from pathlib import Path
import shutil
import os
import select

from .conf import CONF
from .utils import db
from .utils import check_error
from .utils.amqp import get_connection, consume

LOG = logging.getLogger('vault')

@check_error
def work(data):
    '''Procedure to handle a message'''

    file_id       = data['file_id']
    user_id       = data['user_id']
    filepath      = Path(data['filepath'])

    # Create the target name from the file_id
    vault_area = Path( CONF.get('vault','location') )
    name = f"{file_id:0>20}" # filling with zeros, and 20 characters wide
    name_bits = [name[i:i+3] for i in range(0, len(name), 3)]
    target = vault_area.joinpath(*name_bits)
    LOG.debug(f'Target: {target}')

    target.parent.mkdir(parents=True, exist_ok=True)

    # Moving the file
    starget = str(target)
    LOG.debug(f'Moving {filepath} to {target}')
    shutil.move(str(filepath), starget)
    
    # Mark it as processed in DB
    db.finalize_file(file_id, starget, target.stat().st_size)

    # Send message to Archived queue
    return { 'file_id': file_id } # I could have the details in here. Fetching from DB instead.

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    connection = get_connection('local.broker')
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        consume( channel,
                 work,
                 from_queue = CONF.get('local.broker','completed_queue'),
                 to_channel = channel,
                 to_exchange= CONF.get('local.broker','exchange'),
                 to_routing = CONF.get('local.broker','routing_archived'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
