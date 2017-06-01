#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Connecting to Central EGA to Local EGA
#
####################################

Connects to message broker A,
picks a message and
re-publish it in message broker B.
'''

import sys
import logging
import argparse

from .conf import CONF
from . import amqp as broker

LOG = logging.getLogger('connect')

def main():

    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser(description="Forward message between CentralEGA's broker and the local one",
                                     allow_abbrev=False)
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')

    group = parser.add_argument_group(title='Compulsary components for the forwarding connection')
    group.add_argument('--from-domain',    dest='from_domain',     required=True)
    group.add_argument('--from-queue',     dest='from_queue',      required=True)
    group.add_argument('--to-domain',      dest='to_domain',       required=True)
    group.add_argument('--to-exchange',    dest='to_exchange',     required=True)
    group.add_argument('--to-routing-key', dest='to_routing_key',  required=True)

    args = parser.parse_args()

    LOG.info(f'Connection {args.from_domain} to {args.to_domain}')

    from_queue  = CONF.get(args.from_domain,args.from_queue)
    to_exchange = CONF.get(args.to_domain,args.to_exchange)
    to_routing  = CONF.get(args.to_domain,args.to_routing_key)

    LOG.debug(f'From queue: {from_queue}')
    LOG.debug(f'To exchange: {to_exchange}')
    LOG.debug(f'To routing key: {to_routing}')

    from_connection = broker.get_connection(args.from_domain)
    from_channel = from_connection.channel()

    to_connection = broker.get_connection(args.to_domain)
    to_channel = to_connection.channel()
    to_channel.basic_qos(prefetch_count=1) # One job at a time

    LOG.info(f'Forwarding messages')

    try:
        broker.forward(from_channel,
                       from_queue  = from_queue,
                       to_channel  = to_channel,
                       to_exchange = to_exchange,
                       to_routing  = to_routing)
    except KeyboardInterrupt:
        from_channel.stop_consuming()
    finally:
        to_connection.close()
        to_connection.close()

if __name__ == '__main__':
    main()
