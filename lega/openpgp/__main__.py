#!/usr/bin/env python3.6 -u
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

        LOG.debug(f"###### Encrypted file: {args.filename}")
        with open(args.filename, 'rb') as infile:
            name = cipher = session_key = None
            for packet in iter_packets(infile):
                LOG.debug(str(packet))
                if packet.tag == 1:
                    LOG.debug("###### Decrypting session key")
                    # Note: decrypt_session_key knows the key ID.
                    #       It will be updated to contact the keyserver
                    #       and retrieve the private_key material
                    connection = CONF.get('ingestion','keyserver_connection')
                    ssl_ctx = ssl.create_default_context()
                    ssl_ctx.check_hostname = False
                    ssl_ctx.verify_mode=ssl.CERT_NONE
                    def fetch_private_key(key_id):
                        LOG.info(f'Retrieving the PGP Private Key {key_id}')
                        keyurl = f'{connection}/retrieve/pgp/{key_id}'
                        try:
                            req = Request(keyurl, headers={'content-type':'application/json'}, method='GET')
                            LOG.info(f'Opening connection to {keyurl}')
                            with urlopen(req, context=ssl_ctx) as response:
                                data = json.loads(response.read().decode())
                                public_key_material = bytes.fromhex(data['public'])
                                private_key_material = bytes.fromhex(data['private'])
                            # Connection closed
                            return make_key(public_key_material, private_key_material)
                        except HTTPError as e:
                            LOG.critical(f'Unknown PGP key {key_id}')
                            sys.exit(1)

                    name, cipher, session_key = packet.decrypt_session_key(fetch_private_key)
                    LOG.info(f'SESSION KEY: {session_key.hex()}')

                elif packet.tag == 18:
                    LOG.info(f"###### Decrypting message using {name}")
                    assert( session_key and cipher )
                    for literal_data in packet.process(session_key, cipher):
                        sys.stdout.buffer.write(literal_data)
                else:
                    packet.skip()
    except PGPError as pgpe:
        LOG.critical(str(pgpe))
        sys.exit(2)


if __name__ == '__main__':
    # import cProfile
    # cProfile.run('main()', 'ega-pgp.profile')
    main()


