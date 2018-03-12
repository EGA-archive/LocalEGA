# -*- coding: utf-8 -*-

import sys
import io
import logging
from datetime import datetime, timedelta
import hashlib

from .constants import lookup_pub_algorithm, lookup_sym_algorithm, lookup_hash_algorithm, lookup_s2k, lookup_tag
from .utils import (PGPError,
                    read_1_byte, read_2_bytes, read_4_bytes,
                    new_tag_length, old_tag_length,
                    get_mpi, parse_public_key_material, parse_private_key_material, pack_key_material,
                    derive_key,
                    decryptor, make_decryptor,
                    decompressor,
                    validate_private_data)
from .iobuf import IOBuf

LOG = logging.getLogger('openpgp')


PACKET_TYPES = {} # Will be updated below

def parse_next_packet(data):
    """\
    A packet is composed of (in order) a `tag`, a `length` and a `body`.

    A tag is one byte long and determine how many bytes the length is.

    There are two formats for tag:
    * old style: The length can be 0, 1, 2 or 4 byte(s) long.
    * new style: The length can be 1, 2, or 4 byte(s) long.
 
    Packet Tag byte
    ---------------
    +-------------+----------+---------------+---+---+---+---+---------+---------+
    | bit         | 7        | 6             | 5 | 4 | 3 | 2 | 1       | 0       |
    +-------------+----------+---------------+---+---+---+---+---------+---------+
    |             | always 1 | packet format |               | length type       |
    |             |          |               |               | 0 = 1 byte        |
    | old-style   |          |       0       |  packet tag   | 1 = 2 bytes       |
    |             |          |               |               | 2 = 5 bytes       |
    |             |          |               |               | 3 = undertermined |
    +-------------+          +---------------+---------------+-------------------+
    |             |          |               |                                   |
    | new-style   |          |       1       |             packet tag            |
    |             |          |               |                                   |
    +-------------+----------+---------------+-----------------------------------+

    With the old format, the tag includes the length, but the number of packet types is limited to 16.
    With the new format, the number of packet type can exceed 16, and the length are the following bytes.

    The length determines how many bytes the body is.
    Note that the new format can specify a length that encodes a body chunk by chunk.
   
    Refer to RFC 4880 for more information (https://tools.ietf.org/html/rfc4880).
    """
    org_pos = data.tell()

    # First byte
    b = data.read(1)
    if not b:
        return None

    #LOG.debug(f"First byte: {b.hex()} {ord(b):08b} ({ord(b)})")
    b = ord(b)

    # 7th bit of the first byte must be a 1
    if not bool(b & 0x80):
        rest = data.read()
        LOG.debug(f'REST ({len(rest)} bytes): {rest.hex()}')
        raise PGPError("incorrect packet header")

    # the header is in new format if bit 6 is set
    new_format = bool(b & 0x40)

    # tag encoded in bits 5-0 (new packet format)
    tag = b & 0x3f

    if new_format:
        # length is encoded in the second (and following) octet
        data_length, partial = new_tag_length(data)
    else:
        tag >>= 2 # tag encoded in bits 5-2, discard bits 1-0
        length_type = b & 0x03 # get the last 2 bits
        data_length, partial = old_tag_length(data, length_type)

    PacketType = PACKET_TYPES.get(tag, Packet)
    start_pos = data.tell()
    return PacketType(tag, new_format, data_length, partial, org_pos, start_pos, data)

def iter_packets(data):
    while True:
        packet = parse_next_packet(data)
        if packet is None:
            break
        yield packet

def consume():
    '''Main generator to parse and process a stream of data.

    The one advancing it sends the generator a pair of data and a
    boolean to tell if it is the last chunk.
    '''
    LOG.debug('Starting a stream processor')
    stream = IOBuf()
    data, more_coming = yield # wait
    stream.write(data)
    while True:
        #LOG.debug('Advancing the stream processor | more_coming: {more_coming}')
        packet = parse_next_packet(stream)
        if packet is None:
            LOG.debug('No more packet')
            del stream
            return
        try:
            LOG.debug('FOUND a %s', packet.name)
            gen = packet.process()
            next(gen) # start it
            data, more_coming = yield gen.send(more_coming)
            while True:
                stream.write(data)
                data, more_coming = yield gen.send(more_coming)
        except StopIteration:
            LOG.debug('DONE processing packet %s', packet.name)
        # recurse

    
class Packet(object):
    '''The base packet object containing various fields pulled from the packet
    header as well as a slice of the packet data.'''
    def __init__(self, tag, new_format, length, partial, org_pos, start_pos, data):
        self.tag = tag
        self.new_format = new_format
        self.length = length # just for printing
        self.org_pos = org_pos
        self.start_pos = start_pos
        self.partial = partial
        self.data = data # open file
        self.name = lookup_tag(self.tag)

    def skip(self):
        self.data.seek(self.start_pos, io.SEEK_SET) # go to start of data
        self.data.seek(self.length, io.SEEK_CUR) # skip data
        partial = self.partial
        LOG.debug(f'data length {self.length} - partial {self.partial} | {self.name}')
        while partial:
            data_length, partial = new_tag_length(self.data)
            LOG.debug(f'data length {data_length} - partial {partial} | {self.name}')
            self.length += data_length
            self.data.seek(data_length, io.SEEK_CUR) # skip data

    def parse(self): # Overloaded in subclasses
        self.skip()

    def __str__(self):
        return "#{} | tag {:2} | {} bytes | pos {} ({}) | {}".format("new" if self.new_format else "old",
                                                                     self.tag,
                                                                     self.length,
                                                                     self.org_pos, self.start_pos,
                                                                     self.name)

    def __repr__(self):
        return "#{} | tag {:2} | {} bytes | pos {} ({}) | {}".format("new" if self.new_format else "old",
                                                                     self.tag,
                                                                     self.length,
                                                                     self.org_pos, self.start_pos,
                                                                     self.name)


class PublicKeyPacket(Packet):

    def parse(self):
        assert( not self.partial )
        self.pubkey_version = read_1_byte(self.data)
        if self.pubkey_version in (2,3):
            raise PGPError("Warning: version 3 keys are deprecated")
        elif self.pubkey_version != 4:
            raise PGPError(f"Unsupported public key packet, version {self.pubkey_version}")

        self.raw_creation_time = read_4_bytes(self.data)
        self.creation_time = datetime.utcfromtimestamp(self.raw_creation_time)
        # No validity, moved to Signature

        # Parse the key material and remember it in buffer self.public_part. Used by private_packet.unlock()
        self.public_part = io.BytesIO()
        self.raw_pub_algorithm, self.pub_algorithm_type, *material = parse_public_key_material(self.data, buf=self.public_part)

        # Hashing only the public part (differs from self.length for private key packets)
        size = self.data.tell() - self.start_pos
        sha1 = hashlib.sha1()
        sha1.update(bytearray( (0x99, (size >> 8) & 0xff, size & 0xff) )) # 0x99 and the 2-octet length
        self.data.seek(self.start_pos, io.SEEK_SET) # rewind
        sha1.update(self.data.read(size))
        self.fingerprint = sha1.hexdigest().upper()
        self.key_id = self.fingerprint[-16:] # lower 64 bits

    def __repr__(self):
        s = super().__repr__()
        return f"{s}\n\t| {self.creation_time} \n\t| KeyID {self.key_id} (ver 4)({lookup_pub_algorithm(self.raw_pub_algorithm)[0]})\n\t| {self.pub_algorithm_type.upper()} key"


class SecretKeyPacket(PublicKeyPacket):
    s2k_usage = None
    s2k_type = None
    s2k_iv = None
    s2k_hash = None

    def parse_s2k(self):
        self.s2k_type = read_1_byte(self.data)
        if self.s2k_type == 0:
            # simple string-to-key
            hash_algo = read_1_byte(self.data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)

        elif self.s2k_type == 1:
            # salted string-to-key
            hash_algo = read_1_byte(self.data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)
            # 8 bytes salt
            self.s2k_salt = self.data.read(8)

        elif self.s2k_type == 2:
            # reserved
            pass

        elif self.s2k_type == 3:
            # iterated and salted
            hash_algo = read_1_byte(self.data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)
            self.s2k_salt = self.data.read(8)
            self.s2k_coded_count = read_1_byte(self.data)
            self.s2k_count = (16 + (self.s2k_coded_count & 15)) << ((self.s2k_coded_count >> 4) + 6)

        elif 100 <= self.s2k_type <= 110:
            raise PGPError("GNU experimental: Not Implemented")
        else:
            raise PGPError(f"Unsupported public key algorithm {self.s2k_type}")

    def unlock(self, passphrase):
        assert( not self.partial )

        # parse the public part
        super().parse()

        # parse secret-key packet format from section 5.5.3
        self.s2k_usage = read_1_byte(self.data)

        if self.s2k_usage == 0:
            # key data not encrypted
            self.s2k_hash = lookup_hash_algorithm("MD5")
            parse_private_key_material(self.raw_pub_algorithm, self.data) # just consume
            self.checksum = read_2_bytes(self.data)
        elif self.s2k_usage in (254, 255):
            # string-to-key specifier
            self.cipher_id = read_1_byte(self.data)
            self.s2k_cipher, _, alg = lookup_sym_algorithm(self.cipher_id)
            self.s2k_iv_len = alg.block_size // 8
            self.parse_s2k()
            # Get the IV
            self.s2k_iv = self.data.read(self.s2k_iv_len)

            self.private_data = self.data.read(self.length + self.start_pos - self.data.tell()) # includes 2-bytes checksum or the 20-bytes hash
            self.sha1chk = (self.s2k_usage == 254)
            
        else:
            # it is a symmetric-key encryption algorithm identifier
            self.s2k_cipher, _, alg = lookup_sym_algorithm(self.s2k_usage)
            self.s2k_iv_len = alg.block_size // 8
            # Get the IV
            self.s2k_iv = self.data.read(self.s2k_iv_len)

        # So, skip to the right place anyway
        self.data.seek(self.start_pos + self.length, io.SEEK_SET)

        # Ready to unlock the private parts
        name, key_len, cipher = lookup_sym_algorithm(self.cipher_id)
        iv_len = cipher.block_size // 8
        LOG.debug("Unlocking seckey: %s (keylen: %i bytes) | IV %s (%i bytes)", name, key_len, self.s2k_iv.hex(), iv_len)
        assert( len(self.s2k_iv) == iv_len )
        passphrase_key = derive_key(passphrase, key_len, self.s2k_type, self.s2k_hash, self.s2k_salt, self.s2k_count)
        LOG.debug("derived passphrase key: %s", passphrase_key.hex())
        #LOG.debug("derived passphrase key length: %i bytes", len(passphrase_key))

        assert(len(passphrase_key) == key_len)
        engine = make_decryptor(passphrase_key, cipher, self.s2k_iv)
        clear_private_data = bytes(engine.update(self.private_data) + engine.finalize())
        
        validate_private_data(clear_private_data, self.s2k_usage)
        LOG.info('Passphrase correct')

        # Packing the return data
        return pack_key_material(self.public_part, io.BytesIO(clear_private_data))

    def __repr__(self):
        s = super().__repr__()

        s2f = "S2K ERROR on type {type}"
        if self.s2k_type == 0:
            s2f = "S2K {cipher} - {type} - {hash}"
        elif self.s2k_type == 1:
            s2f = "S2K {cipher} - {type} - {hash} - {salt}"
        elif self.s2k_type == 2:
            s2 = "reserved"
        elif self.s2k_type == 3:
            s2f = "S2K {cipher} - {type} - {hash} - {salt} - {count} ({coded_count})"

        s2 = s2f.format(cipher=self.s2k_cipher,
                        usage=self.s2k_usage,
                        type=lookup_s2k(self.s2k_type)[0],
                        hash=self.s2k_hash,
                        salt=self.s2k_salt.hex(),
                        count=self.s2k_count,
                        coded_count=self.s2k_coded_count)

        return f"{s} \n\t| {s2} \n\t| IV {self.s2k_iv.hex()}"


class UserIDPacket(Packet):
    '''A User ID packet consists of UTF-8 text that is intended to represent
    the name and email address of the key holder. By convention, it includes an
    RFC 2822 mail name-addr, but there are no restrictions on its content.'''
    def parse(self):
        assert( not self.partial )
        self.info = self.data.read(self.length).decode('utf8')

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | {self.info}"

class PublicKeyEncryptedSessionKeyPacket(Packet):

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | keyID {self.key_id} ({lookup_pub_algorithm(self.raw_pub_algorithm)[0]})"

    def decrypt_session_key(self, call_keyserver):
        assert( not self.partial )
        pos_start = self.data.tell()
        session_key_version = read_1_byte(self.data)
        if session_key_version != 3:
            raise PGPError(f"Unsupported encrypted session key packet, version {session_key_version}")

        self.key_id = self.data.read(8).hex()
        self.raw_pub_algorithm = read_1_byte(self.data)
        # Remainder is the encrypted key
        self.encrypted_data = get_mpi(self.data)

        private_key, private_padding = call_keyserver(self.key_id)

        key_args = (private_padding, ) if private_padding else ()
        try:
            session_data = private_key.decrypt(self.encrypted_data, *key_args)
                
            session_data = io.BytesIO(session_data)
            symalg_id = read_1_byte(session_data)

            name, keylen, symalg = lookup_sym_algorithm(symalg_id)
            symkey = session_data.read(keylen)

            LOG.debug("%s | %i | Session key: %s", name, keylen, symkey.hex())
            assert( keylen == len(symkey) )
            checksum = read_2_bytes(session_data)
            
            if not sum(symkey) % 65536 == checksum:
                raise PGPError(f"{name} decryption failed")

            return (name, symalg, symkey)
        except ValueError as e:
            raise PGPError(str(e))


class SymEncryptedDataPacket(Packet):
    
    def __repr__(self):
        s = super().__repr__()
        return f"{s} | version {self.version}"
    
    # See 5.13 (page 50)
    def process(self, session_key, cipher):
        '''Generator producing the literal data stepwise, as a bytes object,
           by reading the encrypted data chunk by chunk.

        For example, move it forward to completion as:
        >>> for literal_data in packet.process(session_key, cipher):
        >>>         sys.stdout.buffer.write(literal_data)

        '''
        
        # Initialization
        self.engine = decryptor(session_key, cipher)
        self.prefix_size = next(self.engine) # start it
        self.prefix_found = False
        self.prefix = b''
        self.prefix_count = 0
        self.mdc = (self.tag == 18)
        self.hasher = hashlib.sha1() if self.mdc else None
        consumer = consume()
        next(consumer) # start it

        # Skip over the compulsary version byte
        self.version = read_1_byte(self.data)
        assert( self.version == 1 )

        # Do-until.
        data_length, final = self.length - 1, not self.partial
        while True:
            # Produce data
            LOG.debug('Reading data to decrypt: %i bytes - final %s', data_length, final)
            encrypted_data = (self.data.read(data_length), data_length, final)
            assert( len(encrypted_data[0]) == encrypted_data[1] )
            decrypted_data = self.engine.send(encrypted_data)
            decrypted_data = self._handle_decrypted_data(decrypted_data, final)

            # Consume and return data
            literal_data = consumer.send( (decrypted_data, final) )
            if literal_data:
                yield literal_data

            # More coming?
            if not final:
                data_length, partial = new_tag_length(self.data)
                final = not partial
            else:
                break

        # Finally, MDC control
        if self.mdc:
            digest = b'\xD3\x14' + self.hasher.digest() # including prefix, and MDC tag+length
            LOG.debug('digest: %s', digest.hex())
            LOG.debug('   MDC: %s', self.mdc_value.hex())
            if self.mdc_value != digest:
                raise PGPError("MDC Decryption failed")

        LOG.debug('decryption finished')

    def _handle_decrypted_data(self, data, final):
        '''Strip the prefix and MDC value when they arrive,
           and send the data to the hasher.'''

        if not self.prefix_found:
            self.prefix_count += len(data)

        if self.mdc and final:
            assert(self.prefix_count >= (22 + self.prefix_size))
            self.mdc_value = data[-22:]
            data = data[:-20]
            
        if self.mdc:
            self.hasher.update(data)

        # Handle prefix
        if not self.prefix_found and self.prefix_count > self.prefix_size:
            self.prefix = data[:self.prefix_size]
            LOG.debug('PREFIX: %s', self.prefix.hex())
            if self.prefix[-4:-2] != self.prefix[-2:]:
                raise PGPError("Prefix Repetition error")
            self.prefix_found = True
            data = data[self.prefix_size:]

        return data

class CompressedDataPacket(Packet):

    def process(self):
        '''Generator producing the literal data stepwise, as a bytes object,
           by decompressing data chunk by chunk.

           It is usually not started alone. Instead, the process()
           generator above will initialize it and move it forward.  It
           is then used as a internal and specialized version for the
           main process() generator.
        '''

        LOG.debug('Initializing Decompressor')
        more_coming = yield

        algo = read_1_byte(self.data)
        LOG.debug('Compression Algo: %s', algo)
        engine = decompressor(algo)

        consumer = consume()
        next(consumer) # start it

        data_length, final = (self.length - 1 if self.length else None), not self.partial

        if data_length is None:
            LOG.debug('Undetermined length')
            assert( final )

        while True:
            LOG.debug('Reading data to decompress | buffer size %i', self.data.get_size())
            data = self.data.read(data_length)
            LOG.debug('Got some data to decompress: %i | final %s', len(data), final)

            if data_length is not None:
                data_length -= len(data)

            if data_length:
                LOG.debug('The body of that packet is not yet complete | Need %i left | %s', data_length, self.name)

            decompressed_data = engine.decompress(data)
            LOG.debug('Decompressed data: %i', len(decompressed_data))

            if final or not more_coming:
                LOG.debug('Not more coming: Flushing the decompressor')
                decompressed_data += engine.flush()
                
            more_coming = yield consumer.send( (decompressed_data,final or more_coming) )

            if data_length:
                continue

            if not final: # must continue
                assert( data_length == 0 ) # and data_length is not None
                data_length, partial = new_tag_length(self.data)
                final = not partial
                assert( data_length is not None )
            else:
                # data_length could be None
                # In that case, my parent tells me if I should exit
                # and if there are data in the buffer when I wake up
                # Otherwise I wait, until more data is available in Da stream
                if data_length is None and self.data.get_size() > 0:
                    continue
                
                if not more_coming:
                    LOG.debug('no more coming: finito | %s', self.name)
                    break
                yield # nothing


        LOG.debug('decompression finished')

class LiteralDataPacket(Packet):

    def process(self):

        LOG.debug('Processing %s', self.name)
        more_coming = yield # ready to work

        # TODO: Handle the case where there is not enough data.
        # ie the buffer contains less than filename+6 bytes
        assert( self.data.get_size() > 6 )

        self.data_format = self.data.read(1)
        LOG.debug('data format: %s', self.data_format.decode())

        filename_length = read_1_byte(self.data)
        if filename_length == 0:
            filename = None
        else:
            filename = self.data.read(filename_length)
            assert( len(filename) == filename_length )
            # if filename == '_CONSOLE': # then sensitive file
            #     filename = None

        if filename:
            LOG.debug('filename: %s', filename)

        self.raw_date = read_4_bytes(self.data)
        self.date = datetime.utcfromtimestamp(self.raw_date)
        LOG.debug('date: %s', self.date)

        LOG.debug('Literal packet length %i | partial %s', self.length, self.partial)
        data_length, final = (self.length-6-filename_length if self.length else None), not self.partial

        if data_length is None:
            LOG.debug('Undetermined length')
            assert( final )

        while True:
            data = self.data.read(data_length)
            LOG.debug('Literal length: %i - final %s', data_length, final)
            assert( data )

            if data_length is not None:
                data_length -= len(data)

            if data_length:
                LOG.debug('The body of that packet is not yet complete | Need %i left | %s', data_length, self.name)

            LOG.debug('Got some literal data: %i', len(data))
            more_coming = yield data

            if data_length:
                continue

            if not final:
                assert( data_length is not None and data_length == 0 )
                data_length, partial = new_tag_length(self.data)
                assert( data_length is not None )
                final = not partial
            else:
                # data_length could be None
                # In that case, my parent tells me if I should exit
                # and if there are data in the buffer when I wake up
                # Otherwise I wait, until more data is available in Da stream
                if data_length is None and self.data.get_size() > 0:
                    continue
                
                if not more_coming:
                    LOG.debug('no more coming: finito | %s', self.name)
                    break
                yield # nothing

        LOG.debug('DONE with %s', self.name)

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | format {self.data_format}"
    
class TrustPacket(Packet):
    def __init__(self, *args, **kwargs):
        raise PGPError("TrustPacket (tag 12) should not be exported outside keyrings")


PACKET_TYPES = {
    1: PublicKeyEncryptedSessionKeyPacket,
    # 2: SignaturePacket,
    5: SecretKeyPacket,
    6: PublicKeyPacket,
    7: SecretKeyPacket,
    8: CompressedDataPacket,
    9: SymEncryptedDataPacket,
    11: LiteralDataPacket,
    12: TrustPacket,
    13: UserIDPacket,
    14: PublicKeyPacket,
    # 17: UserAttributePacket,
    18: SymEncryptedDataPacket,
}
    
