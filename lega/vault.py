#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Listener moving files from staging area to vault.

It simply consumes message from ``staged`` queue and upon completion,
sends a message to the local exchange with the routing key :``archived``.
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

    file_id       = data['internal_data']['file_id']
    user_id       = data['internal_data']['user_id']
    filepath      = Path(data['internal_data']['filepath'])

    # Create the target name from the file_id
    vault_area = Path(CONF.get_or_else('vault', 'path'))
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
    data['internal_data'] = file_id # I could have the details in here. Fetching from DB instead.
    data['status'] = { 'state': 'ARCHIVED', 'message': 'File moved to the vault' }
    return data

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    consume(work, 'staged', 'archived')

if __name__ == '__main__':
    main()
