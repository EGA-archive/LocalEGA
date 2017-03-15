#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import json
import traceback

from lega.conf import CONF
from lega import crypto
from lega import amqp as broker

LOG = logging.getLogger(__name__)

#CONF.setup()

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

        # reply = {
        #     'filepath': data['target']
        #     'submission_id': data['submission_id'],
        #     'user_id': data['user_id']
        # }
        # LOG.debug("Reply message: {}".format(reply))
        # return json.dumps(reply)
        return body

    except Exception as e:
        LOG.debug("{}: {}".format(e.__class__.__name__, str(e)))
        #if isinstance(e,crypto.Error) or isinstance(e,OSError):

        traceback.print_exc()
        raise e


def main(args=None):

    if not os.environ.get('GPG_AGENT_INFO', None):
        print("GPG_AGENT_INFO is undefined, so the gpg-agent will be unreachable", file=sys.stderr)
        return 2

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf
    CONF.log_setup(LOG,'worker')
    crypto.setup()
    CONF.log_setup(crypto.LOG,'crypto')
    broker.setup()
    CONF.log_setup(broker.LOG,'message.broker')

    broker.consume(
        broker.process(work),
        from_queue = CONF.get('worker','todo_queue')
    )
    return 0

if __name__ == '__main__':
    sys.exit( main() )

