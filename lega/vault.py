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

When a message is consumed, it must be of the form:
* filepath
* submission_id
* user_id

This service should probably also implement a stort of StableID generator,
and input that in the database.
'''

import sys
import logging
import json
from pathlib import Path
import shutil

from .conf import CONF
from . import db
from . import amqp as broker

LOG = logging.getLogger('vault')

def work(data):
    '''Procedure to handle a message'''

    file_id       = data['file_id']
    submission_id = data['submission_id']
    user_id       = data['user_id']
    filepath      = Path(data['filepath'])
    
    vault_area = Path( CONF.get('vault','location') )
    name = data['target_name']
    name_bits = [name[i:i+3] for i in range(0, len(name), 3)]
    LOG.debug(f'Name bits: {name_bits!r}')
    target = vault_area.joinpath(*name_bits)
    LOG.debug(f'Target: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    LOG.debug('Target parent: {}'.format(target.parent))
    starget = str(target)
    shutil.move(str(filepath), starget)
    
    # Mark it as processed in DB
    db.finalize_file(file_id, starget, target.stat().st_size)

    # TODO: Mark the checksums as good, so we don't re-process this file

    # Make the workers clean the folder
    reply = { 'task' : 'clean', 'folder': str(filepath.parent) }
    LOG.debug(f"Reply message: {reply!r}")
    return json.dumps(reply)


def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    broker.consume( work,
                    from_queue = CONF.get('vault','message_queue'),
                    routing_to = CONF.get('message.broker','routing_done'))

if __name__ == '__main__':
    main()
