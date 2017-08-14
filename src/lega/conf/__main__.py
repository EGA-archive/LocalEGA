#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from . import CONF

def main(args=None):
    """The main routine."""

    if not args:
        args = sys.argv[1:]

    CONF.setup( args )
    print("Main EGA routine")
    print(repr(CONF))
    print("Configuration values:")
    CONF.write(sys.stdout)


if __name__ == "__main__":
    main()
