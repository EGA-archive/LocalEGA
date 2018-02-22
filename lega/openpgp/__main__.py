import sys
import logging

from ..conf import CONF
from .packet import iter_packets

LOG = logging.getLogger('openpgp')

def main(args=None):

    ##################################################################
    # Temporary part that loads the private key and unlocks it
    #
    seckey = "/Users/daz/_ega/deployments/docker/private/swe1/gpg/ega.sec"
    passphrase = "I0jhU1FKoAU76HuN".encode()

    private_key = private_padding = None

    LOG.info(f"###### Opening sec key: {seckey}")
    with open(seckey, 'rb') as infile:
        from .utils import unarmor
        for packet in iter_packets(unarmor(infile)):
            #LOG.info(str(packet))
            if packet.tag == 5:
                #LOG.info("###### Unlocking key with passphrase")
                private_key, private_padding = packet.unlock(passphrase)
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
            LOG.info(str(packet))
            if packet.tag == 1:
                LOG.info("###### Decrypting session key")
                # Note: decrypt_session_key knows the key ID.
                #       It will be updated to contact the keyserver
                #       and retrieve the private_key/private_padding
                # keyserver = CONF.get('ingestion','keyserver')
                # key_id = packet.get_key_id()
                name, cipher, session_key = packet.decrypt_session_key(private_key, private_padding)

            elif packet.tag == 18:
                LOG.info(f"###### Decrypting message using {name}")
                assert( session_key and cipher )
                packet.register(session_key, cipher)
                packet.process()
            else:
                packet.skip()

if __name__ == '__main__':
    #import cProfile
    #cProfile.run('main()', 'openpgp.profile')
    main()


