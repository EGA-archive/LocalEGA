#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Connecting to Central EGA
#
####################################

Connects to CentralEGA message broker,
picks a message and
re-publish it in the local message broker.
'''

import sys
import logging

from .conf import CONF
from . import amqp as broker

LOG = logging.getLogger('cega_connect')

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
        broker.forward(cega_channel,
                       from_queue  = CONF.get('cega.broker','queue'),
                       to_channel  = lega_channel,
                       to_exchange = CONF.get('local.broker','exchange'),
                       to_routing  = CONF.get('local.broker','routing_todo'))
    except KeyboardInterrupt:
        cega_channel.stop_consuming()
    finally:
        lega_connection.close()
        cega_connection.close()

if __name__ == '__main__':
    main()
