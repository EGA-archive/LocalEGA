import sys
import io
import argparse

from .packet import parse, debug
from .utils import unarmor, crc24
from ..exceptions import PGPError

def parsefile(f):
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
        packet = parse(data)
        if packet is None:
            break
        yield packet

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true', default=False)
    parser.add_argument('filename')
    parser.add_argument('seckey')
    parser.add_argument('passphrase')

    args = parser.parse_args()

    if args.d:
        debug()
    
    print("###### Encrypted file",args.filename)
    with open(args.filename, 'rb') as infile:
        for packet in parsefile(infile):
            print(packet)

    print("###### Opening sec key",args.seckey)
    with open(args.seckey, 'rb') as infile:
        for packet in parsefile(infile):
            print(packet)
        

if __name__ == '__main__':
    #import cProfile
    #cProfile.run('main()', 'pgpdump.profile')
    main()
