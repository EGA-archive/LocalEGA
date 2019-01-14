
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate a (random) file in Crypt4GH format"""

import sys
import argparse

import pgpy

from legacryptor.crypt4gh import encrypt


# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-i')
parser.add_argument('-o')
parser.add_argument('size')
parser.add_argument('pk')
args = parser.parse_args()

pubkey, _ = pgpy.PGPKey.from_file(args.pk)
filesize = int(args.size)

class InputFile():
    def __init__(self, inf):
        self.buf = inf
        self.pos = 0

    def read(self, size):
        assert(size>0)

        pos = self.pos + size
        if pos < filesize:
            self.pos = pos
            return self.buf.read(size)

        if self.pos == filesize:
            return b''
        
        b = self.buf.read(filesize - self.pos)
        self.pos = filesize
        return b

infile = open(args.i, 'rb') if args.i else sys.stdin.buffer
outfile = open(args.o, 'wb') if args.o else sys.stdout.buffer
encrypt(pubkey, InputFile(infile), None, outfile)
