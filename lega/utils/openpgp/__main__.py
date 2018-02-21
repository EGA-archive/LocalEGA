import sys
import io
import argparse
import logging

from .packet import iter_packets
from .utils import unarmor as do_unarmor, crc24
from ..exceptions import PGPError

from ...conf import CONF

LOG = logging.getLogger('openpgp')

def unarmor(f):
    # Read the first bytes
    if f.read(5) != b'-----': # is not armored
        f.seek(0,0) # rewind
        data = f
    else: # is armored.
        f.seek(0,0) # rewind
        _, _, data, crc = do_unarmor(bytearray(f.read())) # Yup, fully loading everything in memory
        # verify it if we could find it
        if crc and crc != crc24(data):
            raise PGPError(f"Invalid CRC")
        data = io.BytesIO(data)
    return data

def main(args=None):


    # import pgpy
    # key, _ = pgpy.PGPKey.from_file(seckey)
    # message = pgpy.PGPMessage.from_file(filename)
    # with key.unlock(passphrase.decode()):
    #     print("key unlocked")
    #     m = key.decrypt(message).message
    #     # print(bytes(m).decode())
    #     print("message decrypted")

    # filename = "/Users/daz/_ega/deployments/docker/test/test.gpg"
    seckey = "/Users/daz/_ega/deployments/docker/private/swe1/gpg/ega.sec"
    passphrase = "I0jhU1FKoAU76HuN".encode()

    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('--keyserver', default='http://localhost:9010')
    parser.add_argument('-o','--output', default=None)
    parser.add_argument('filename')
    args = parser.parse_args()

    CONF.setup(['--log','openpgp'])

    outfile, has_outfile = None, False
    try:

        outfile, has_outfile = (open(args.output, 'wb'), True) if args.output else (sys.stdout.buffer, False)

        #seckey = "/Users/daz/_ega/deployments/docker/test/pgp.sec"
        #passphrase = "I0jhU1FKoAU76HuN".encode()

        private_key = private_padding = None
    
        LOG.info(f"###### Opening sec key: {seckey}")
        with open(seckey, 'rb') as infile:
            for packet in iter_packets(unarmor(infile)):
                LOG.info(str(packet))
                if packet.tag == 5:
                    LOG.info("###### Unlocking key with passphrase")
                    private_key, private_padding = packet.unlock(passphrase)
                else:
                    packet.skip()


        LOG.info(f"###### Encrypted file: {args.filename}")
        with open(args.filename, 'rb') as infile:
            name = cipher = session_key = None
            for packet in iter_packets(infile):
                LOG.info(str(packet))
                if packet.tag == 1:
                    LOG.info("###### Decrypting session key")
                    name, cipher, session_key = packet.decrypt_session_key(private_key, private_padding)

                elif packet.tag == 18:
                    LOG.info(f"###### Decrypting message using {name}")
                    assert( session_key and cipher )
                    packet.register(session_key, cipher)
                    packet.process(outfile.write)
                else:
                    packet.skip()

    finally:
        if has_outfile:
            outfile.close()

if __name__ == '__main__':
    #import cProfile
    #cProfile.run('main()', 'pgpdump.profile')
    main()


