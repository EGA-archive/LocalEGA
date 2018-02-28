#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-

import sys
import logging

from ..conf import CONF
from .packet import iter_packets
from .utils import make_key

LOG = logging.getLogger('openpgp')

def main(args=None):

    ##################################################################
    # Temporary part that loads the private key and unlocks it
    #
    seckey = "/Users/daz/_ega/deployments/docker/private/swe1/gpg/ega.sec"
    passphrase = "I0jhU1FKoAU76HuN".encode()
    private_key_material = None
    LOG.info(f"###### Opening sec key: {seckey}")
    with open(seckey, 'rb') as infile:
        from .utils import unarmor
        for packet in iter_packets(unarmor(infile)):
            #LOG.info(str(packet))
            if packet.tag == 5:
                private_key_material = packet.unlock(passphrase)
            else:
                packet.skip()
    #
    # End of the temporary part
    ##################################################################

    if not args:
        args = sys.argv[1:]

    CONF.setup(args)

    filename = args[-1] # Last argument

    LOG.info(f"###### Encrypted file: {filename}")
    with open(filename, 'rb') as infile:
        name = cipher = session_key = None
        for packet in iter_packets(infile):
            #packet.skip()
            LOG.info(str(packet))
            if packet.tag == 1:
                LOG.info("###### Decrypting session key")
                # Note: decrypt_session_key knows the key ID.
                #       It will be updated to contact the keyserver
                #       and retrieve the private_key/private_padding
                # keyserver_url = CONF.get('ingestion','keyserver')
                # res = urllib.request.urlopen(keyserver_url, data=packet.get_key_id())
                # key_alg, *key_material = res.read()
                key_alg, *key_material = private_key_material
                private_key, private_padding = make_key(key_alg, *key_material)
                name, cipher, session_key = packet.decrypt_session_key(private_key, private_padding)

            elif packet.tag == 18:
                LOG.info(f"###### Decrypting message using {name}")
                assert( session_key and cipher )
                for data in packet.process(session_key, cipher):
                    sys.stdout.buffer.write(data)
            else:
                packet.skip()

if __name__ == '__main__':
    #import cProfile
    #cProfile.run('main()', 'openpgp.profile')
    main()


