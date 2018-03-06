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

sec_key = ''
passphrase = b''

def fetch_private_key(key_id):
    # ssl_ctx = ssl.create_default_context()
    # ssl_ctx.check_hostname = False
    # ssl_ctx.verify_mode=ssl.CERT_NONE
    # connection = CONF.get('ingestion','keyserver_connection')
    # LOG.info(f'Retrieving the PGP Private Key {key_id}')
    # keyurl = f'{connection}/retrieve/pgp/{key_id}'
    # try:
    #     req = Request(keyurl, headers={'content-type':'application/json'}, method='GET')
    #     LOG.info(f'Opening connection to {keyurl}')
    #     with urlopen(req, context=ssl_ctx) as response:
    #         data = json.loads(response.read().decode())
    #         public_key_material = bytes.fromhex(data['public'])
    #         private_key_material = bytes.fromhex(data['private'])
    #     LOG.info(f'Connection to the server closed for {key_id}')
    #     return make_key(public_key_material, private_key_material)
    # except HTTPError as e:
    #     LOG.critical(f'Unknown PGP key {key_id}')
    #     sys.exit(1)

    from .utils import unarmor
    with open(sec_key, 'rb') as infile:
        for packet in iter_packets(unarmor(infile)):
            LOG.info(str(packet))
            if packet.tag == 5:
                public_key_material, private_key_material = packet.unlock(passphrase)
            else:
                packet.skip()
    return make_key(public_key_material, private_key_material)


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

        parser.add_argument('-s',help='Private key')
        parser.add_argument('-p',help='Passphrase')

        args = parser.parse_args()

        global sec_key
        sec_key = args.s
        global passphrase
        passphrase = args.p.encode()

        LOG.debug(f"###### Encrypted file: {args.filename}")
        with open(args.filename, 'rb') as infile:
            name = cipher = session_key = None
            for packet in iter_packets(infile):
                LOG.debug(str(packet))
                if packet.tag == 1:
                    LOG.debug("###### Decrypting session key")
                    # Note: decrypt_session_key does not know yet the key ID.
                    #       It will parse the packet and then contact the keyserver
                    #       to retrieve the private_key material
                    name, cipher, session_key = packet.decrypt_session_key(fetch_private_key)
                    LOG.info('{0} SESSION KEY: {1} {0}'.format('*'*30, session_key.hex()))

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


