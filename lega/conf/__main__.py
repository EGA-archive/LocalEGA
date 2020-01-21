#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from . import CONF


def main(print_values=False):
    """Run the main routine, for loading configuration."""

    print(repr(CONF))

    if print_values:
        print("\nConfiguration values:")
        CONF.write(sys.stdout)


if __name__ == "__main__":
    main(print_values=len(sys.argv) > 1 and sys.argv[1] == 'list')
