#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Generate a public/private PGP key pair.'''

import sys
import argparse

from lega.openpgp.generate import generate_pgp_key, output_key

def main():

    parser = argparse.ArgumentParser(description='''Creating public/private PGP keys''')

    parser.add_argument('name', help='PGP user name')
    parser.add_argument('email', help='PGP user email')
    parser.add_argument('comment', help='PGP user comment')

    parser.add_argument('--passphrase', help='Password to protect the private key. If none, the key is left unlocked')

    parser.add_argument('--pub', help='Output file for public key [Default: stdout]')
    parser.add_argument('--priv', help='Output file for private key [Default: stdout]')

    # Armored by default
    #parser.add_argument('--binary', action='store_true')
    parser.add_argument('--armor', '-a', action='store_true', help='ASCII armor the output')

    args = parser.parse_args()
    
    pub_key, priv_key = generate_pgp_key(args.name, args.email, args.comment, passphrase=args.passphrase, armor=args.armor)
    
    output_key(args.pub, pub_key, armor=args.armor)
    output_key(args.priv, priv_key, armor=args.armor)
    

if __name__ == '__main__':
    main()
