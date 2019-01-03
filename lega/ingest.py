#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Worker reading messages from the ``files`` queue, splitting the Crypt4GH header from the remainder of the file.

The header is stored in the database and the remainder is sent to the backend storage:
either a regular file system or an S3 object store.

It is possible to start several workers.

When a message is consumed, it must at least contain the following fields:

* ``filepath``
* ``user_id``

Upon completion, a message is sent to the local exchange with the
routing key :``archived``.
"""

import sys
import logging
from pathlib import Path
from functools import partial

from legacryptor.crypt4gh import get_header

from .conf import CONF
from .utils import db, exceptions, sanitize_user_id, storage
from .utils.amqp import consume, publish, get_connection

LOG = logging.getLogger(__name__)


@db.catch_error
@db.crypt4gh_to_user_errors
def work(fs, inbox_fs, channel, data):
    """Read a message, split the header and send the remainder to the backend store."""
    filepath = data['filepath']
    LOG.info(f"Processing {filepath}")

    # Remove the host part of the user name
    user_id = sanitize_user_id(data['user'])

    # Keeping data as-is (cuz the decorator is using it)
    # It will be augmented, but we keep the original data first
    org_msg = data.copy()
    data['org_msg'] = org_msg

    # Insert in database
    file_id = db.insert_file(filepath, user_id)
    data['file_id'] = file_id  # must be there: database error uses it

    # Instantiate the inbox backend
    inbox = inbox_fs(user_id)
    LOG.info("Inbox backend: %s", inbox)

    # Check if file is in inbox
    if not inbox.exists(filepath):
        raise exceptions.NotFoundInInbox(filepath)  # return early

    # Ok, we have the file in the inbox

    # Record in database
    db.mark_in_progress(file_id)

    # Sending a progress message to CentralEGA
    org_msg['status'] = 'PROCESSING'
    LOG.debug(f'Sending message to CentralEGA: {data}')
    publish(org_msg, channel, 'cega', 'files.processing')
    org_msg.pop('status', None)

    # Strip the header out and copy the rest of the file to the vault
    LOG.debug('Opening %s', filepath)
    with inbox.open(filepath, 'rb') as infile:
        LOG.debug(f'Reading header | file_id: {file_id}')
        beginning, header = get_header(infile)

        header_hex = (beginning+header).hex()
        data['header'] = header_hex
        db.store_header(file_id, header_hex)  # header bytes will be .hex()

        target = fs.location(file_id)
        LOG.info(f'[{fs.__class__.__name__}] Moving the rest of {filepath} to {target}')
        target_size = fs.copy(infile, target)  # It will copy the rest only

        LOG.info(f'Vault copying completed. Updating database')
        db.set_archived(file_id, target, target_size)
        data['vault_path'] = target

    LOG.debug(f"Reply message: {data}")
    return data


def main(args=None):
    """Run ingest service."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)  # re-conf

    inbox_fs = getattr(storage, CONF.get_value('inbox', 'driver', default='FileStorage'))
    fs = getattr(storage, CONF.get_value('vault', 'driver', default='FileStorage'))
    broker = get_connection('broker')
    do_work = partial(work, fs(), partial(inbox_fs, 'inbox'), broker.channel())

    # upstream link configured in local broker
    consume(do_work, broker, 'files', 'archived')


if __name__ == '__main__':
    main()
