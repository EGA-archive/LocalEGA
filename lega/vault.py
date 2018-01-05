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
from pathlib import Path
import shutil

from .conf import CONF
from .utils import db
from .utils.amqp import consume


LOG = logging.getLogger('vault')

@db.catch_error
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

    consume(work, 'staged', 'archived')

if __name__ == '__main__':
    main()
