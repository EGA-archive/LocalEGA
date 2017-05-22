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
from pathlib import Path
import shutil
import stat

from .conf import CONF
from . import crypto
from . import amqp as broker
from . import db
from .utils import (
    get_data as parse_data,
    get_inbox,
    get_staging_area,
    checksum
)

LOG = logging.getLogger('worker')

def work(data):
    '''Verifying that the file in the vault does decrypt properly'''

    # # remove parent folder if empty
    # try:
    #     shutil.rmdir(str(folder)) # raise exception is not empty
    #     LOG.debug(f'Removing {filepath.parent!s}')
    # except OSError:
    #     pass
    pass
    
def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    cega_connection = broker.get_connection('cega.broker')
    cega_channel = cega_connection.channel()

    lega_connection = broker.get_connection('local.broker')
    lega_channel = lega_connection.channel()
    lega_channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        broker.consume(lega_channel,
                       work,
                       from_queue  = CONF.get('local.broker','archived_queue'),
                       to_channel  = cega_channel,
                       to_exchange = CONF.get('cega.broker','exchange'),
                       to_routing  = CONF.get('cega.broker','routing_to'))
    except KeyboardInterrupt:
        lega_channel.stop_consuming()
    finally:
        lega_connection.close()
        cega_connection.close()

if __name__ == '__main__':
    main()
