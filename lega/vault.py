#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Listener moving files to the Vault
#
####################################

It simply consumes message from the message queue configured in the [vault] section.

It defaults to the `completed` queue.

When a message is consumed, it must be of the form:
* filepath
* submission_id
* user_id

This service should probably also implement a stort of StableID generator,
and input that in the database.
'''

import sys
import os
import logging
import json
import traceback
from pathlib import Path
import requests

from .conf import CONF
from . import crypto
from . import amqp as broker
from . import utils

LOG = logging.getLogger('vault')

def work(message_id, body):

    LOG.debug(f"Processing message: {message_id}")
    try:

        data = json.loads(body)

        submission_id = data['submission_id']
        user_id       = data['user_id']
        filepath      = Path(data['filepath'])

        vault_area = Path( CONF.get('vault','location') )
        vault_area.mkdir(parents=True, exist_ok=True) # re-create

        name = requests.get('http://{}:{}/'.format(CONF.get('namer','host',fallback='localhost'),
                                                   CONF.get('namer','port',fallback=8080)),
                            headers={'X-LocalEGA-Sweden':'yes'})

        target = vault_area / name
        filepath.rename(target) # move

        # Mark it as processed in DB
        # TODO

        return None

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
        from_queue = CONF.get('vault','message_queue')
    )
    return 0

if __name__ == '__main__':
    sys.exit( main() )
