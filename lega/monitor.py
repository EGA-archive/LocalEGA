#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Monitoring the error queues
#
####################################

So far, we only log the messages.

Note: we can configure the logger to send emails :-)
'''

import sys
import logging
import argparse
    
from .conf import CONF
from . import amqp as broker

LOG = None

def sys_work(data):
    '''Procedure to handle a message'''
    LOG.debug(data)
    return None

def user_work(data):
    '''Procedure to handle a message'''
    LOG.debug(data)
    return None

def main():

    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser()
    # parser.add_argument('--conf', action='store', help='Where to conf is', default=None)
    # parser.add_argument('--log',  action='store', help='Where to log is',  default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--sys',  action='store_true', help='Monitor all the system errors' )
    group.add_argument('--user', action='store_true', help='Monitor errors from the users' )
    args = parser.parse_args()

    if args.sys:
        LOG = logging.getLogger('sys-monitor')
        broker.consume( sys_work, from_queue = CONF.get('monitor','sys_errors'))

    if args.user:
        LOG = logging.getLogger('user-monitor')
        broker.consume( user_work, from_queue = CONF.get('monitor','user_errors'))

