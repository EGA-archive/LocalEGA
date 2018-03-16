#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Decrypting file from the vault, given a stable ID.
#
# Only used for testing to see if:
# * the encrypted file can be decrypted
# * the decrypted content matches the original file (by comparing the checksums)
#
####################################
'''

import sys
import logging
from urllib.request import urlopen
#import tempfile
import json

from .conf import CONF
from .utils import db, checksum
from .utils.crypto import decrypt_from_vault

LOG = logging.getLogger('outgestion')

def get_master_key():
    keyurl = CONF.get('ingestion','keyserver_endpoint_rsa')
    LOG.info(f'Retrieving the Master Public Key from {keyurl}')
    try:
        # Prepare to contact the Keyserver for the Master key
        with urlopen(keyurl) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        LOG.error(repr(e))
        LOG.critical('Problem contacting the Keyserver. Ingestion Worker terminated')
        sys.exit(1)

def get_info(fileid):
    # put your dirty hands in the database
    with db.connect() as conn:
        with conn.cursor() as cur:
            query = 'SELECT org_checksum, org_checksum_algo, filepath from files WHERE stable_id = %(file_id)s;'
            cur.execute(query, { 'file_id': fileid})
            return cur.fetchone()


def main(args=None):
    print("====== JUST FOR TESTING =======", file=sys.stderr)
    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    master_key = get_master_key() # might exit

    LOG.info(f"Master Key ID: {master_key['id']}")
    LOG.debug(f"Master Key: {master_key}")

    stable_id = args[-1]
    LOG.debug(f"Requested stable ID: {stable_id}")
    org_checksum, org_checksum_algo, filepath = get_info(stable_id)
    LOG.debug(f"Orginal {org_checksum_algo} checksum: {org_checksum}")
    LOG.debug(f"Vault path: {filepath}")

    # Decrypting
    with open(filepath,'rb') as infile: #tempfile.TemporaryFile() as outfile, 
        hasher = checksum.instantiate(org_checksum_algo)
        decrypt_from_vault(infile, master_key, hasher=hasher) # outfile=None
        
        # Check integrity of decrypted file
        if org_checksum != hasher.hexdigest():
            print("Aiiieeee...bummer.... Invalid checksum")
            sys.exit(2)
        else:
            sys.stdout.buffer.write(b"All good \xF0\x9F\x91\x8D\n")


if __name__ == '__main__':
    main()
