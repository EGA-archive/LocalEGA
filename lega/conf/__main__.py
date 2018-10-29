#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse

from . import CONF

def main(args=None):
    """The main routine."""

    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Forward message between CentralEGA's broker and the local one",
                                     allow_abbrev=False)
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log',  help='configuration file for the loggers')
    
    parser.add_argument('--list', dest='list_content', action='store_true', help='Lists the content of the configuration file')
    pargs = parser.parse_args(args)
    
    CONF.setup( args )

    print(repr(CONF))

    if pargs.list_content:
        print("\nConfiguration values:")
        CONF.write(sys.stdout)


if __name__ == "__main__":
    main()
