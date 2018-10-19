#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse

from . import Configuration


def main(args=None):
    """Run the main routine, for loading configuration."""
    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Forward message between CentralEGA's broker and the local one",
                                     allow_abbrev=False)
    parser.add_argument('--conf', help='configuration file, in INI or YAML format')
    parser.add_argument('--log', help='configuration file for the loggers')

    parser.add_argument('--list', dest='list_content', action='store_true', help='Lists the content of the configuration file')
    pargs = parser.parse_args(args)

    conf = Configuration()
    conf.setup(args)

    print(repr(conf))

    if pargs.list_content:
        print("\nConfiguration values:")
        conf.write(sys.stdout)


if __name__ == "__main__":
    main()
