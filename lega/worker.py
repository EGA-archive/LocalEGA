#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import json
import traceback

from .conf import CONF
from . import crypto
from . import amqp as broker

LOG = logging.getLogger('worker')

def work(message_id, body):

    LOG.debug("Processing message: {}".format(message_id))
    try:

        data = json.loads(body)

        crypto.ingest( data['filepath'],
                       data['hash'],
                       hash_algo = data['hash_algo'],
                       target = data['target']
        )

        LOG.debug("Done with message {}".format(message_id))

        reply = {
            'filepath': data['target'],
            'submission_id': data['submission_id'],
            'user_id': data['user_id'],
        }
        LOG.debug(f"Reply message: {reply!r}")
        return json.dumps(reply)

    except Exception as e:
        LOG.debug(f"{e.__class__.__name__}: {e!s}")
        #if isinstance(e,crypto.Error) or isinstance(e,OSError):
        traceback.print_exc()
        raise e


def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    broker.consume(
        broker.process(work),
        from_queue = CONF.get('worker','message_queue')
    )
    return 0

if __name__ == '__main__':
    sys.exit( main() )

