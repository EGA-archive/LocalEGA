#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import json
import traceback

from .conf import CONF
from . import crypto
from . import amqp as broker
from . import utils

LOG = logging.getLogger(__name__)

def work(message_id, body):

    LOG.debug(f"Processing message: {message_id}")
    try:

        data = json.loads(body)

        utils.to_vault( data['target'],
                        data['submission_id'],
                        data['user_id']
        )

        # Mark it as processed in DB

        return None

    except Exception as e:
        LOG.debug("{}: {}".format(e.__class__.__name__, str(e)))
        #if isinstance(e,crypto.Error) or isinstance(e,OSError):

        traceback.print_exc()
        raise e


def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf
    CONF.log_setup(LOG,'vault')
    broker.setup()
    CONF.log_setup(broker.LOG,'message.broker')

    broker.consume(
        broker.process(work),
        from_queue = CONF.get('vault','message_queue')
    )
    return 0

if __name__ == '__main__':
    sys.exit( main() )
