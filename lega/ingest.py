#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Worker reading messages from the ``files`` queue, splitting the
Crypt4GH header from the remainder of the file.  The header is stored
in the database and the remainder is sent to the backend storage:
either a regular file system or an S3 object store.

It is possible to start several workers.

When a message is consumed, it must at least contain the following fields:

* ``filepath``
* ``stable_id``
* ``user_id``

Optionally an integrity field, called ``unencrypted_integrity``, can be added, with:

* ``checksum`` value
* ``algorithm`` - the associated hash algorithm

Upon completion, a message is sent to the local exchange with the
routing key :``archived``.

'''

import sys
import logging
from pathlib import Path
from functools import partial

from legacryptor.crypt4gh import get_header

from .conf import CONF
from .utils import db, exceptions, checksum, sanitize_user_id, storage
from .utils.amqp import consume, publish, get_connection

LOG = logging.getLogger(__name__)

def run_checksum(data, integrity, filename):
    LOG.info('Checksuming %s', filename)
    try:
        i = data[integrity]
        h = i['checksum']
        algo = i['algorithm']
        if not algo: # Fix in case CentralEGA sends null
            algo = 'md5'
    except (KeyError, TypeError):
        LOG.info('Finding a companion file')
        h, algo = checksum.get_from_companion(filename)
        data[integrity] = {'checksum': h, 'algorithm': algo }

        assert( isinstance(h,str) )
        assert( isinstance(algo,str) )

        # Check integrity of encrypted file
        LOG.debug(f"Verifying the {algo} checksum of file: {filename}")
        if not checksum.is_valid(filename, h, hashAlgo = algo):
            LOG.error(f"Invalid {algo} checksum for {filename}")
            raise exceptions.Checksum(algo, file=filename, decrypted=False)
        LOG.debug(f'Valid {algo} checksum for {filename}')

@db.catch_error
@db.crypt4gh_to_user_errors
def work(fs, channel, data):
    '''Reads a message, splits the header and sends the remainder to the backend store.'''

    filepath = data['filepath']
    stable_id = data['stable_id']
    LOG.info(f"Processing {filepath} (with stable_id: {stable_id})")

    # Use user_id, and not elixir_id
    user_id = sanitize_user_id(data['user'])

    # Insert in database
    file_id = db.insert_file(filepath, user_id, stable_id)

    org_msg = data.copy()
    data.update({
        'file_id': file_id,
        'user_id': user_id,
        'org_msg': org_msg,
    })

    # Find inbox
    inbox = Path(CONF.get_value('inbox', 'location', raw=True) % user_id)
    LOG.info(f"Inbox area: {inbox}")

    # Check if file is in inbox
    inbox_filepath = inbox / filepath
    if not inbox_filepath.exists():
        raise exceptions.NotFoundInInbox(filepath) # return early

    # Ok, we have the file in the inbox

    # Get the checksum
    if CONF.get_value('ingestion', 'do_checksum', conv=bool, default=False):
        run_checksum(data, 'encrypted_integrity', inbox_filepath)

    # Record in database
    db.set_status(file_id, db.Status.In_Progress)

    # Sending a progress message to CentralEGA
    data['status'] = db.Status.In_Progress.value
    org_msg['status'] = { 'state': 'PROCESSING', 'details': None }
    LOG.debug(f'Sending message to CentralEGA: {data}')
    publish(org_msg, channel, 'cega', 'files.processing')
    org_msg.pop('status', None)
    
    # Strip the header out and copy the rest of the file to the vault
    LOG.debug(f'Opening {inbox_filepath}')
    with open(inbox_filepath, 'rb') as infile:
        LOG.debug(f'Reading header | file_id: {file_id}')
        beginning, header = get_header(infile)

        target = fs.location(file_id)
        LOG.info(f'[{fs.__class__.__name__}] Moving the rest of {filepath} to {target}')
        target_size = fs.copy(infile, target) # It will copy the rest only

        LOG.info(f'Vault copying completed. Updating database')
        header_hex = (beginning+header).hex()
        db.set_info(file_id, target, target_size, header_hex) # header bytes will be .hex()
        data['header'] = header_hex
        data['vault_path'] = target
        data['vault_type'] = fs.__class__.__name__
        data['status'] = db.Status.Archived.value

    LOG.debug(f"Reply message: {data}")
    return data

def main(args=None):
    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    fs = getattr(storage, CONF.get_value('vault', 'driver', default='FileStorage'))
    broker = get_connection('broker')
    do_work = partial(work, fs(), broker.channel())

    # upstream link configured in local broker
    consume(do_work, broker, 'files', 'archived')

if __name__ == '__main__':
    main()
