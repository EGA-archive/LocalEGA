import sys
import io
import argparse
import logging

from .packet import parse
from .utils import unarmor, crc24
from ..exceptions import PGPError

from ...conf import CONF

LOG = logging.getLogger('openpgp')

def parsefile(f,fout):
    # Read the first bytes
    if f.read(5) != b'-----': # is not armored
        f.seek(0,0) # rewind
        data = f
    else: # is armored.
        f.seek(0,0) # rewind
        _, _, data, crc = unarmor(bytearray(f.read())) # Yup, fully loading everything in memory
        # verify it if we could find it
        if crc and crc != crc24(data):
            raise PGPError(f"Invalid CRC")
        data = io.BytesIO(data)

    while True:
        packet = parse(data, fout)
        if packet is None:
            break
        yield packet

def main(args=None):

    if not args:
        args = sys.argv[1:]

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-d', action='store_true', default=False)
    # # parser.add_argument('filename')
    # # parser.add_argument('seckey')
    # # parser.add_argument('passphrase')

    # args = parser.parse_args()

    #CONF.setup(args)
    CONF.setup(['--log',None])

    filename = "/Users/daz/_ega/deployments/docker/test/spoof.gpg"
    seckey = "/Users/daz/_ega/deployments/docker/test/pgp.sec"
    passphrase = "Unguessable".encode()

    # import pgpy
    # key, _ = pgpy.PGPKey.from_file(seckey)
    # message = pgpy.PGPMessage.from_file(filename)
    # with key.unlock(passphrase.decode()):
    #     print("key unlocked")
    #     m = key.decrypt(message).message
    #     # print(bytes(m).decode())
    #     print("message decrypted")

    # filename = "/Users/daz/_ega/deployments/docker/test/test.gpg"
    # seckey = "/Users/daz/_ega/deployments/docker/private/swe1/gpg/ega.sec"
    # passphrase = "I0jhU1FKoAU76HuN".encode()

    private_packet = None
    
    LOG.info(f"###### Opening sec key: {seckey}")
    with open(seckey, 'rb') as infile, open(filename + '.org', 'wb') as outfile:
        for packet in parsefile(infile, outfile):
            LOG.info(packet)
            if packet.tag == 5:
                private_packet = packet
                LOG.info("###### Unlocking key with passphrase")
                private_packet.unlock(passphrase)


    LOG.info(f"###### Encrypted file: {filename}")
    with open(filename, 'rb') as infile, open(filename + '.org', 'wb') as outfile:
        data_packet = None
        for packet in parsefile(infile, outfile):
            LOG.info(packet)
            if packet.tag == 1:
                session_packet = packet

            if packet.tag == 18:
                data_packet = packet

        LOG.info("###### Decrypting session key")
        name, cipher, session_key = session_packet.decrypt_session_key(private_packet)
        LOG.info(f"###### Decrypting message using {name}")
        assert( data_packet and session_key and cipher )

        data_packet.decrypt_message(infile, session_key, cipher)
        

if __name__ == '__main__':
    #import cProfile
    #cProfile.run('main()', 'pgpdump.profile')
    main()


