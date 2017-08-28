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
from .utils.amqp import get_connection, forward
from .utils import set_file_id, sanitize_user_id

LOG = logging.getLogger('connect')

_from_cega_to_lega = {
    'cega:lega:users': (('cega.broker','sweden.v1.commands.user','local.broker','lega','lega.users'), {'transform':sanitize_user_id}),
    'cega:lega:files': (('cega.broker','sweden.v1.commands.file','local.broker','lega','lega.tasks'), {'transform':set_file_id}),
    'lega:cega:users': (('local.broker','verified','cega.broker','localega.v1','sweden.file.completed'),{}),
    'lega:cega:files': (('local.broker','account', 'cega.broker','localega.v1','sweden.user.account'),{}),
}

def _connect(from_domain, from_queue, to_domain, to_exchange, to_routing, transform=None):

    if transform and isinstance(transform,str):
        transform = getattr(sys.modules[__name__], transform, None)

    if transform:
        LOG.debug(f'Transform function: {transform}')

    from_connection = get_connection(from_domain)
    from_channel = from_connection.channel()

    to_connection = get_connection(to_domain)
    to_channel = to_connection.channel()
    to_channel.basic_qos(prefetch_count=1) # One job at a time

    LOG.info(f'Forwarding messages')

    try:
        forward(from_channel,
                from_queue  = from_queue,
                to_channel  = to_channel,
                to_exchange = to_exchange,
                to_routing  = to_routing,
                transform   = transform)
    except KeyboardInterrupt:
        from_channel.stop_consuming()
    finally:
        to_connection.close()
        to_connection.close()

def connect(args=None):

    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Forward message from a (broker,queue) to a (broker,exchange,routing_key)",
                                     allow_abbrev=False)
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')
    parser.add_argument('connection',
                        action='store',
                        choices=list(_from_cega_to_lega.keys()),
                        help='Special values')
    pargs = parser.parse_args()

    CONF.setup(args) # re-conf

    connection,kwargs = _from_cega_to_lega[pargs.connection] # Should be there!

    LOG.info(f'Connection {connection[0]} to {connection[2]}')
    LOG.debug(f'From queue: {connection[1]}')
    LOG.debug(f'To exchange: {connection[3]}')
    LOG.debug(f'To routing key: {connection[4]}')

    _connect(*connection, **kwargs)

def main(args=None):

    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Forward message from a (broker,queue) to a (broker,exchange,routing_key)",
                                     allow_abbrev=False)
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')
    parser.add_argument('--transform', default=None)

    group_in = parser.add_argument_group(title='Arguments for the incoming connection')
    group_in.add_argument('from_domain')
    group_in.add_argument('from_queue')
    group_out = parser.add_argument_group(title='Arguments for the outgoing connection')
    group_out.add_argument('to_domain')
    group_out.add_argument('to_exchange')
    group_out.add_argument('to_routing')

    pargs = parser.parse_args()

    CONF.setup(args) # re-conf

    LOG.info(f'Connection {pargs.from_domain} to {pargs.to_domain}')
    LOG.debug(f'From queue: {pargs.from_queue}')
    LOG.debug(f'To exchange: {pargs.to_exchange}')
    LOG.debug(f'To routing key: {pargs.to_routing}')

    _connect(pargs.from_domain, pargs.from_queue,
            pargs.to_domain, pargs.to_exchange, pargs.to_routing,
            transform=pargs.transform)

if __name__ == '__main__':
    main()
