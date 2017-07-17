#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Monitoring the errors
#
####################################

So far, we only log the messages.

Note: we can configure the logger to send emails :-)
'''

import sys
import logging
import argparse
from time import sleep
    
from .conf import CONF
from .utils import db

LOG = None

def sys_work(data):
    '''Procedure to handle a message'''
    LOG.debug(data)
    return None

def user_work(data):
    '''Procedure to handle a message'''
    LOG.debug(data)
    return None

def check_errors(handle_error,interval):
    while True:
        errors = db.get_errors()
        for error in errors:
            LOG.info(repr(error))
        sleep(interval)

def main():
    global LOG
    CONF.setup(sys.argv[1:]) # re-conf

    parser = argparse.ArgumentParser()
    # parser.add_argument('--conf', action='store', help='Where to conf is', default=None)
    # parser.add_argument('--log',  action='store', help='Where to log is',  default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--sys',  action='store_true', help='Monitor all the system errors' )
    group.add_argument('--user', action='store_true', help='Monitor errors from the users' )
    args = parser.parse_args()


    interval = CONF.getint('monitor','interval', fallback=600) # default 10min
    if args.sys:
        LOG = logging.getLogger('sys-monitor')
        handle_error = sys_work
        
    if args.user:
        LOG = logging.getLogger('user-monitor')
        handle_error = user_work

    check_errors(handle_error,interval)

if __name__ == '__main__':
    main()
