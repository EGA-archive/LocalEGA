#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Re-Encryption Worker
#
####################################

It simply consumes message from the message queue configured in the [worker] section of the configuration files.

It defaults to the `tasks` queue.

It is possible to start several workers, of course!
However, they should have the gpg-agent socket location in their environment (when using GnuPG 2.0 or less).
In GnuPG 2.1, it is not necessary (Just point the `homedir` to the right place).

When a message is consumed, it must be of the form:
* filepath
* target
* hash (of the unencrypted content)
* hash_algo: the associated hash algorithm
'''

import sys
import os
import logging
import json

from .conf import CONF
from . import crypto
from . import amqp as broker
from . import db

LOG = logging.getLogger('worker')

def work(data):
    '''Procedure to handle a message'''

    file_id = data['file_id']
    db.update_status(file_id, db.Status.In_Progress)

    try:
        details, target_digest, reenc_key = crypto.ingest( data['source'],
                                                           data['hash'],
                                                           hash_algo = data['hash_algo'],
                                                           target = data['target'])
        db.set_encryption(file_id, details, reenc_key)

        reply = {
            'file_id' : file_id,
            'filepath': data['target'],
            'target_name': target_digest,
            'submission_id': data['submission_id'],
            'user_id': data['user_id'],
        }
        LOG.debug(f"Reply message: {reply!r}")
        return json.dumps(reply)

    except Exception as e:
        LOG.debug(f"{e.__class__.__name__}: {e!s}")
        db.set_error(file_id, e)

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    broker.consume( work,
                    from_queue = CONF.get('worker','message_queue'),
                    routing_to = CONF.get('message.broker','routing_complete'))

if __name__ == '__main__':
    main()
