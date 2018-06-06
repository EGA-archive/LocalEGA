#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Worker reading messages from the ``files`` queue, decrypting and
re-encrypting inbox files into a staging area.

It is possible to start several workers.

When a message is consumed, it must be of the form:

* ``filepath``
* ``stable_id``
* ``user_id``

and optionally an integrity field, called ``unencrypted_integrity``, with:

* ``checksum`` value
* ``algorithm`` - the associated hash algorithm

Upon completion, a message is sent to the local exchange with the
routing key :``staged``.
'''

import sys
import logging
from pathlib import Path
import shutil

from .conf import CONF
from .utils import db, exceptions, checksum, sanitize_user_id
from .utils.amqp import consume, publish, get_connection

from legacryptor.crypt4gh import get_header

LOG = logging.getLogger(__name__)

def run_checksum(data, integrity, filename):
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
def work(data):
    '''Ingestion function

    The data is of the form:

    * user id
    * a filepath
    * unencrypted hash information (with both the hash value and the hash algorithm)

    .. note:: The supported hash algorithm are, for the moment, MD5 and SHA256.
    '''

    filepath = data['filepath']
    stable_id = data['stable_id']
    LOG.info(f"Processing {filepath} (with stable_id: {stable_id})")

    # Use user_id, and not elixir_id
    user_id = sanitize_user_id(data['user'])
    
    # Insert in database
    file_id = db.insert_file(filepath, user_id, stable_id)

    # early record
    internal_data = {
        'file_id': file_id,
        'user_id': user_id,
    }
    data['internal_data'] = internal_data

    # Find inbox
    inbox = Path( CONF.get('inbox','location',raw=True) % user_id )
    LOG.info(f"Inbox area: {inbox}")

    # Check if file is in inbox
    inbox_filepath = inbox / filepath
    if not inbox_filepath.exists():
        raise exceptions.NotFoundInInbox(filepath) # return early

    # Ok, we have the file in the inbox

    # Get the checksum
    if CONF.getboolean('ingestion','do_checksum', fallback=False):
        run_checksum(data, 'encrypted_integrity', inbox_filepath)

    # Sending a progress message to CentralEGA
    data['status'] = { 'state': 'PROCESSING', 'details': None }
    LOG.debug(f'Sending message to CentralEGA: {data}')
    broker = get_connection('broker')
    publish(data, broker.channel(), 'cega', 'files.processing')

    # Strip the header out and copy the file to the vault
    with open(inbox_filepath, 'rb') as infile:
        header = get_header(infile)

        vault_area = Path( CONF.get('vault','location') )
        name = f"{file_id:0>20}" # filling with zeros, and 20 characters wide
        name_bits = [name[i:i+3] for i in range(0, len(name), 3)]
        target = vault_area.joinpath(*name_bits)
        LOG.debug(f'Target: {target}')
        target.parent.mkdir(parents=True, exist_ok=True)

        # Moving the file
        starget = str(target)
        LOG.debug(f'Moving the rest of {filepath} to {target}')
        with open(starget, 'wb') as outfile:
            shutil.copyfileobj(infile, outfile) # It will copy the rest only

        LOG.debug(f'Vault copying completed')
        internal_data['filepath'] = starget

    LOG.debug(f"Reply message: {data}")
    return data

def main(args=None):
    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    # upstream link configured in local broker
    consume(work, 'files', 'staged')

if __name__ == '__main__':
    main()
