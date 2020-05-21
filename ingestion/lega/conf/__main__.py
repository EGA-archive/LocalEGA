#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if __name__ == "__main__":

    import sys
    from . import CONF

    print(repr(CONF))

    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        print("\nConfiguration values:")
        CONF.write(sys.stdout)
