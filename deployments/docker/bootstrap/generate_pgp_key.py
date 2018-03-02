#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Generate a public/private PGP key pair.'''

import sys
import argparse

from pgpy import PGPKey, PGPUID
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm

parser = argparse.ArgumentParser(description='''Creating public/private PGP keys''')

# Armored by default
#parser.add_argument('--binary', action='store_true')

parser.add_argument('name', help='PGP user name')
parser.add_argument('email', help='PGP user email')
parser.add_argument('comment', help='PGP user comment')

parser.add_argument('--passphrase', help='Password to protect the private key. If none, the key is left unlocked')
parser.add_argument('--prefix', help='Output prefix. We append .pub and .sec to it. If none, we output all to stdout.')
parser.add_argument('--armor', '-a', action='store_true', help='ASCII armor the output')


args = parser.parse_args()


# We need to specify all of our preferences because PGPy doesn't have any built-in key preference defaults at this time.
# This example is similar to GnuPG 2.1.x defaults, with no expiration or preferred keyserver
key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
uid = PGPUID.new(args.name, email=args.email, comment=args.comment)
key.add_uid(uid,
            usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
            hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512, HashAlgorithm.SHA224],
            ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
            compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP, CompressionAlgorithm.Uncompressed])

# Protecting the key
if args.passphrase:
    key.protect(args.passphrase, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
else:
    print('WARNING: Unprotected key', file=sys.stderr)

pub_data = str(key.pubkey) if args.armor else bytes(key.pubkey) # armored or not
sec_data = str(key) if args.armor else bytes(key) # armored or not

if args.prefix:
    with open(f'{args.prefix}.pub', 'w' if args.armor else 'bw') as pub:
        pub.write(pub_data)
    with open(f'{args.prefix}.sec', 'w' if args.armor else 'bw') as sec:
        sec.write(sec_data)
else: #stdout
    output = sys.stdout if args.armor else sys.stdout.buffer
    output.write(pub_data)
    output.write(sec_data)
