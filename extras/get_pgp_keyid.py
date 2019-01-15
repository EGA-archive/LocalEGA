#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Retrieve the keyid from a pgp key file.'''

import sys
import pgpy

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <file> <passphrase>", file=sys.stderr)
        sys.exit(2)

    key, _ = pgpy.PGPKey.from_file(sys.argv[1])
    assert not key.is_public, f"The key {name} should be private"
    with key.unlock(sys.argv[2]) as k:
        key_id = k.fingerprint.keyid.upper()
        print(key_id)
