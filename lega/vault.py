#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import json
import traceback

import lega.conf
import lega.amqp as broker

CONF = conf.CONF
LOG = logging.getLogger(__name__)

def work(message_id, body):

    LOG.debug("Processing message: {}".format(message_id))
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

        traceback.print_exc()
        raise e

    LOG.debug("Done with message {}".format(message_id))

def main(args=None):

    if not os.environ['GPG_AGENT_INFO']:
        sys.exit(2)

    if not args:
        args = sys.argv[1:]
    conf.setup(args)
    conf.log_setup(LOG,'vault')

    broker.consume(
        broker.process(work),
        from_queue = CONF.get('vault','todo_queue')
    )

if __name__ == '__main__':
    import sys
    sys.exit( main() )
