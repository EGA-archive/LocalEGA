#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json

from ..defs import get_file_content, generate_bcrypt_hash


def main(name, user_id, passphrase):

    # Bcrypt hash
    passphrase_hash=generate_bcrypt_hash(get_file_content(passphrase, mode='rt'))
        
    json.dump({
	"username" : name,
	"uid" : int(user_id),
	"passwordHash" : passphrase_hash.decode(),
        "gecos" : f"LocalEGA user {name}",
  	"sshPublicKey" : sys.stdin.read().strip(),
	"enabled" : None
    },sys.stdout, indent=4)

if __name__ == '__main__':
    main(*sys.argv[1:])
