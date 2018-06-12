#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Generate a public/private PGP key pair.'''

import sys
import argparse

from pgpy import PGPKey, PGPUID
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm

def generate_pgp_key(name, email, comment, passphrase=None, armor=True):
    # We need to specify all of our preferences because PGPy doesn't have any built-in key preference defaults at this time.
    # This example is similar to GnuPG 2.1.x defaults, with no expiration or preferred keyserver
    key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
    uid = PGPUID.new(name, email=email, comment=comment)
    key.add_uid(uid,
                usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
                hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512, HashAlgorithm.SHA224],
                ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
                compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP, CompressionAlgorithm.Uncompressed])
    
    # Protecting the key
    if passphrase:
        key.protect(passphrase, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
    else:
        print('WARNING: Unprotected key', file=sys.stderr)
        
    pub_data = str(key.pubkey) if armor else bytes(key.pubkey) # armored or not
    sec_data = str(key) if armor else bytes(key) # armored or not

    return (pub_data, sec_data)

def output_key(f_path, data, armor=True):
    if f_path:
        with open(f_path, 'w' if armor else 'bw') as f:
            f.write(data)
    else: #stdout
        output = sys.stdout if armor else sys.stdout.buffer
        output.write(data)

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
