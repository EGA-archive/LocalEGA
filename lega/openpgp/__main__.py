#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import json
import ssl
import argparse

from ..conf import CONF
from .packet import iter_packets
from .utils import make_key, PGPError

LOG = logging.getLogger('openpgp')

def fetch_private_key(key_id):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode=ssl.CERT_NONE
    LOG.info('Retrieving the PGP Private Key %s', key_id)
    keyurl = CONF.get('ingestion','keyserver_endpoint_pgp',raw=True) % key_id
    try:
        req = Request(keyurl, headers={'content-type':'application/json'}, method='GET')
        LOG.info('Opening connection to %s', keyurl)
        with urlopen(req, context=ssl_ctx) as response:
            data = json.loads(response.read().decode())
        LOG.info('Connection to the server closed for %s', key_id)
        return make_key(data)
    except HTTPError as e:
        LOG.critical('Unknown PGP key %s', key_id)
        sys.exit(1)

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args)

    try:
        # Parser to enforce the filename
        parser = argparse.ArgumentParser(description='''Decrypt a PGP message.''')
        parser.add_argument('--log', help="The logger configuration file")
        parser.add_argument('--conf', help="The EGA configuration file")
        parser.add_argument('filename', help="The path of the file to decrypt")

        args = parser.parse_args()

        LOG.debug("###### Encrypted file: %s", args.filename)
        with open(args.filename, 'rb') as infile:
            name = cipher = session_key = None
            for packet in iter_packets(infile):
                LOG.debug(str(packet))
                if packet.tag == 1:
                    LOG.debug("###### Decrypting session key")
                    # Note: decrypt_session_key does not know yet the key ID.
                    #      It will parse the packet and then use the provided function,
                    #      fetch_private_key, to retrieve the private_key material
                    name, cipher, session_key = packet.decrypt_session_key(fetch_private_key)
                    LOG.info('SESSION KEY: %s', session_key.hex())

                elif packet.tag == 18:
                    LOG.info("###### Decrypting message using %s", name)
                    assert( session_key and cipher )
                    for literal_data in packet.process(session_key, cipher):
                        sys.stdout.buffer.write(literal_data)
                else:
                    packet.skip()
    except PGPError as pgpe:
        LOG.critical(str(pgpe))
        sys.exit(2)


if __name__ == '__main__':
    main()


