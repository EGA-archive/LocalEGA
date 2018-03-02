#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-

import sys
import logging
# from urllib.request import urlopen
# import json

from ..conf import CONF
from .packet import iter_packets
from .utils import make_key, PGPError

LOG = logging.getLogger('openpgp')

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args)

    try:
        # ##################################################################
        # # Temporary part that loads the private key and unlocks it
        # #
        # # seckey = "/Users/daz/_ega/deployments/docker/private/swe1/gpg/ega.sec"
        # # passphrase = "I0jhU1FKoAU76HuN".encode()
        # seckey = "/etc/ega/pgp/sec.pem"
        # passphrase = "8RYJtXsU4qc3lmAi".encode()
        # public_key_material = private_key_material = None
        # LOG.info(f"###### Opening sec key: {seckey}")
        # with open(seckey, 'rb') as infile:
        #     from .utils import unarmor
        #     for packet in iter_packets(unarmor(infile)):
        #         LOG.info(str(packet))
        #         if packet.tag == 5:
        #             public_key_material, private_key_material = packet.unlock(passphrase)
        #             LOG.info('============================= KEY ID: %s',packet.key_id)
        #         else:
        #             packet.skip()
        # #
        # # End of the temporary part
        # ##################################################################
        # sys.exit(2)

        filename = args[-1] # Last argument

        LOG.debug(f"###### Encrypted file: {filename}")
        with open(filename, 'rb') as infile:
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
                    LOG.info('Retrieving the PGP Private Key')
                    keyurl = f'{connection}/retrieve/pgp/{packet.key_id}'
                    req = urllib.request.Request(keyurl, headers={'content-type':'application/json'}, method='GET')
                    LOG.info(f'Opening connection to {keyurl}')
                    with urlopen(req, context=ssl_ctx) as response:
                        data = json.loads(response.read().decode))
                        public_key_material = bytes.fromhex(data['public'])
                        private_key_material = bytes.fromhex(data['private'])
                    # Connection closed
                    private_key, private_padding = make_key(public_key_material, private_key_material)
                    name, cipher, session_key = packet.decrypt_session_key(private_key, private_padding)
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


