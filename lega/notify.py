#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Send message to the local broker about file events.

 Messages are JSON formatted as

 {
                  'user': <str>,
              'filepath': <str>,
             'operation': ( "upload" | "remove" | "rename" ),
              'filesize': <num>,
               'oldpath': <str>, // Ignored if not "rename"
    'file_last_modified': <num>, // a UNIX timestamp
   'encrypted_checksums': [{ 'type': <str>, 'value': <checksum as HEX> },
                           { 'type': <str>, 'value': <checksum as HEX> },
                           ...
                          ]
 }

The checksum algorithm type is 'md5', or 'sha256'.
'sha256' is preferred.

.. note:: This is helping the helpdesk on the Central EGA side.
"""

import sys
import logging
from functools import partial

from .conf import CONF
from .utils import storage
from .utils.amqp import get_connection, publish, consume
from .utils.checksum import calculate_obj

LOG = logging.getLogger(__name__)

def work(fs, channel, data):
    """Read a message, get the filename, the operation and format the inbox message for CentralEGA."""

    filepath = data['filepath']
    user = data['user']
    operation = data['operation']
    LOG.info("Processing %s %s for %s", operation, filepath, user)

    if operation == "upload":
        # Instantiate the inbox backend
        inbox = fs(user)
        LOG.info("Inbox backend: %s", str(inbox))

        assert( inbox.exists(filepath) )

        data['filesize'] = inbox.filesize(filepath)
        data['file_last_modified'] = None # Not yet

        with inbox.open(filepath, 'rb') as infile:
            c = calculate_obj(infile, 'sha256', bsize=8192)
            if c:
                data['encrypted_checksums'] = [{'type': 'sha256', 'value': c}]
    else:
        pass

    # Sending
    publish(data, channel, 'cega', 'files.inbox')
    LOG.debug(f"Sending message: {data}")
    return None


def main(args=None):
    """Run ingest service."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)  # re-conf

    inbox_fs = getattr(storage, CONF.get_value('inbox', 'storage_driver', default='FileStorage'))
    broker = get_connection('broker')
    do_work = partial(work, partial(inbox_fs, 'inbox'), broker.channel())

    # upstream link configured in local broker
    consume(do_work, broker, 'inbox', 'files.inbox')


if __name__ == '__main__':
    main()

