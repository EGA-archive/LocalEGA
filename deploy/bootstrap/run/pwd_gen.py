#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from .defs import generate_password

if __name__ == '__main__':
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    sys.stdout.write(generate_password(size))
