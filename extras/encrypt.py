#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Encrypt a relatively small file, since it loads it in memory.'''

import sys
import argparse

from pgpy import PGPMessage, PGPKey

def main():

    parser = argparse.ArgumentParser(description='''Encrypting a relatively small message''')
    parser.add_argument('pubkey', help='PGP public key')
    parser.add_argument('file', help='File to encrypt')
    args = parser.parse_args()

    message = PGPMessage.new(args.file, file=True)
    key, _ = PGPKey.from_file(args.pubkey)

    enc = key.encrypt(message)
    sys.stdout.buffer.write(bytes(enc))

if __name__ == '__main__':
    main()

