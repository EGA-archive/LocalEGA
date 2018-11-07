#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Worker reading messages from the ``files`` queue, splitting the
Crypt4GH header from the remainder of the file.  The header is stored
in the database and the remainder is sent to the backend storage:
either a regular file system or an S3 object store.

It is possible to start several workers.

When a message is consumed, it must at least contain the following fields:

* ``filepath``
* ``user_id``

Upon completion, a message is sent to the local exchange with the
routing key :``archived``.

'''

import sys
import logging
from pathlib import Path
from functools import partial
import hashlib

from crypt4gh.crypt4gh import Header

from .conf import CONF, configure
from .utils import db, exceptions, errors, checksum, sanitize_user_id, storage
from .utils.amqp import consume, publish

LOG = logging.getLogger(__name__)

@errors.catch(ret_on_error=(None,True))
def _work(fs, correlation_id, data):
    '''Reads a message, splits the header and sends the remainder to the backend store.'''

    # Keeping data as-is (cuz the decorator is using it)
    # It will be augmented, but we keep the original data first
    org_msg = data.copy()
    data['org_msg'] = org_msg

    filepath = data['file_path']
    LOG.info("[%s] Processing %s", correlation_id, filepath)

    # Use user_id, and not elixir_id
    user_id = sanitize_user_id(data['user'])

    # Insert in database (raises Exception if it can't insert)
    file_id = db.insert_file(filepath, user_id) # Mark old insertion as DISABLED too.
    data['file_id'] = file_id # must be there: database error uses it

    # Find inbox
    inbox = Path(CONF.get_value('inbox', 'location', raw=True) % user_id)
    LOG.info("[%s] Inbox area: %s", correlation_id, inbox)

    # Check if file is in inbox
    inbox_filepath = inbox / filepath.lstrip('/')
    LOG.info("[%s] Inbox file path: %s", correlation_id, inbox_filepath)

    # Record in database
    if not inbox_filepath.exists():
        raise exceptions.NotFoundInInbox(filepath) # return early

    # We should change ownership of the file now

    # Ok, we have the file in the inbox: we calculate the checksum too
    md = hashlib.sha256()
    md.update(inbox_filepath.read_bytes())
    db.update(file_id, {'status': 'IN_INGESTION',
                        'inbox_filesize': inbox_filepath.stat().st_size,
                        'inbox_file_checksum': md.hexdigest(),
                        'inbox_file_checksum_type': 'SHA256',
    })

    # Sending a progress message to CentralEGA
    cega_msg = org_msg.copy()
    cega_msg['status'] = 'PROCESSING'
    LOG.debug('[%s] Sending message to CentralEGA: %s', correlation_id, cega_msg)
    publish(cega_msg, 'cega', 'files.processing', correlation_id=correlation_id)
    
    # Strip the header out and copy the rest of the file to the vault
    LOG.debug('[%s] Opening %s', correlation_id, inbox_filepath)
    with open(inbox_filepath, 'rb') as infile:
        LOG.debug('[%s] Reading header | file_id: %s', correlation_id, file_id)
        header = Header.from_stream(infile)

        LOG.info('[%s] Parsed HEADER: %s', correlation_id, header)

        LOG.info('[%s] Adding header to database', correlation_id)
        header_hex = bytes(header).hex()
        data['header'] = header_hex
        db.update(file_id, { 'header': header_hex,
                             'version': header.version })

        target = fs.location(file_id)
        LOG.info(f'[%s] [%s] Moving the rest of %s to %s', correlation_id, fs.__class__.__name__, filepath, target)
        target_size = fs.copy(infile, target) # It will copy the rest only

        LOG.info('[%s] Vault copying completed. Updating database', correlation_id)
        storage_type = None
        if isinstance(fs, storage.S3Storage):
            storage_type = 'S3'
        if isinstance(fs, storage.FileStorage):
            storage_type = 'POSIX'
        db.update(file_id, { 'vault_path': target,
                             'vault_type': storage_type,
                             'vault_filesize': target_size,
                             'status': 'ARCHIVED' })
        data['vault_path'] = target
        data['vault_type'] = storage_type

    LOG.debug("[%s] Reply message: %s", correlation_id, data)
    return (data, False)

@configure
def main():

    fs = getattr(storage, CONF.get_value('vault', 'driver', default='FileStorage'))
    do_work = partial(_work, fs())

    # upstream link configured in local broker
    consume(do_work, 'files', 'archived')

if __name__ == '__main__':
    main()
