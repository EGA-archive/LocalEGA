#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Consumes message to update the database with stable IDs to file IDS mappings.

Instead of building a REST endpoint in front of the database, we
exchange messages between the brokers.

Messages will reliably arrive to the local broker, via the
registered upstream queue.

Note that the upstream is registered via an authenticated mechanism, and uses AMQPS.
'''

from .conf import configure
from .utils import db, errors, sanitize_user_id
from .utils.amqp import consume
from .utils.logging import LEGALogger

LOG = LEGALogger(__name__)

@errors.catch(ret_on_error=(None,True))
def _work(correlation_id, data):
    '''Reads a message containing the ids and add it to the database.'''

    # Adding correlation ID to context
    LOG.add_correlation_id(correlation_id)

    LOG.info("Finalizing Stable ID for %s", data)

    # Clean up username
    data['user'] = sanitize_user_id(data['user'])

    # Translating message from CentralEGA
    _data = { # crash on purpose if KeyError
        'filepath': data['file_path'],
        'user': data['user'],
        'checksum': data['decrypted_checksums'][0]['value'],
        'checksum_type': data['decrypted_checksums'][0]['type'],
        'stable_id': data['stable_id'],
    }

    # Insert stable ID into database
    db.finalize(_data) # might raise error

    # We should revert back the ownership of the file now
    
    LOG.remove_correlation_id()
    # Clean up files is left for the cleanup script. Triggered manually
    return None, False # No result, no error

@configure
def main():
    # upstream link configured in local broker
    consume(_work, 'stableIDs', None, ack_on_error=True) # on error, don't retry the message

if __name__ == '__main__':
    main()
