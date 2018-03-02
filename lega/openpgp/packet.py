# -*- coding: utf-8 -*-

import sys
import io
import logging
from datetime import datetime, timedelta
import hashlib

from ..utils.exceptions import PGPError
from .constants import lookup_pub_algorithm, lookup_sym_algorithm, lookup_hash_algorithm, lookup_s2k, lookup_tag
from .utils import (read_1, read_2, read_4,
                    new_tag_length, old_tag_length,
                    get_mpi, parse_public_key_material, parse_private_key_material,
                    derive_key,
                    decryptor, make_decryptor,
                    decompressor,
                    validate_private_data)
from .iobuf import IOBuf

LOG = logging.getLogger('openpgp')


PACKET_TYPES = {} # Will be updated below

def parse_one(data):
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
        #LOG.debug(f'REST ({len(rest)} bytes): {rest.hex()}')
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
        packet = parse_one(data)
        if packet is None:
            break
        yield packet

def consume():
    '''Main generator to parse and process a stream of data.

    The one advancing it sends the generator a pair of data and a
    boolean to tell if it is the last chunk.
    '''
    #LOG.debug(f'Starting a stream processor')
    stream = IOBuf()
    data, is_final_chunk = yield # wait
    while True:
        stream.write(data)
        #LOG.debug(f'Advancing the stream processor | is_final_chunk {is_final_chunk}')
        packet = parse_one(stream)
        if packet is None:
            #LOG.debug('No more packet')
            del stream
            return
        try:
            #LOG.debug(f'FOUND a {packet.name}')
            engine = packet.process()
            #LOG.debug(f'Created internal engine for the {packet.name}')
            next(engine) # start it
            #LOG.debug(f'engine started | is_final_chunk: {is_final_chunk} | {packet.name}')
            data, is_final_chunk = yield engine.send(is_final_chunk)
            while True:
                stream.write(data)
                data, is_final_chunk = yield engine.send(is_final_chunk)
        except StopIteration:
            pass
            #LOG.debug(f'DONE processing packet: {packet.name}')
        #assert( stream.get_size() == 0 )
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
        #LOG.debug(f'data length {self.length} - partial {self.partial} | {self.name}')
        while partial:
            data_length, partial = new_tag_length(self.data)
            #LOG.debug(f'data length {data_length} - partial {partial} | {self.name}')
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
        self.pubkey_version = read_1(self.data)
        if self.pubkey_version in (2,3):
            raise PGPError("Warning: version 3 keys are deprecated")
        elif self.pubkey_version != 4:
            raise PGPError(f"Unsupported public key packet, version {self.pubkey_version}")

        self.raw_creation_time = read_4(self.data)
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
        self.s2k_type = read_1(self.data)
        if self.s2k_type == 0:
            # simple string-to-key
            hash_algo = read_1(self.data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)

        elif self.s2k_type == 1:
            # salted string-to-key
            hash_algo = read_1(self.data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)
            # 8 bytes salt
            self.s2k_salt = self.data.read(8)

        elif self.s2k_type == 2:
            # reserved
            pass

        elif self.s2k_type == 3:
            # iterated and salted
            hash_algo = read_1(self.data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)
            self.s2k_salt = self.data.read(8)
            self.s2k_coded_count = read_1(self.data)
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
        self.s2k_usage = read_1(self.data)

        if self.s2k_usage == 0:
            # key data not encrypted
            self.s2k_hash = lookup_hash_algorithm("MD5")
            parse_private_key_material(self.raw_pub_algorithm, self.data) # just consume
            self.checksum = read_2(self.data)
        elif self.s2k_usage in (254, 255):
            # string-to-key specifier
            self.cipher_id = read_1(self.data)
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
        #LOG.debug(f"Unlocking seckey: {name} (keylen: {key_len} bytes) | IV {self.s2k_iv.hex()} ({iv_len} bytes)")
        assert( len(self.s2k_iv) == iv_len )
        passphrase_key = derive_key(passphrase, key_len, self.s2k_type, self.s2k_hash, self.s2k_salt, self.s2k_count)
        #LOG.debug(f"derived passphrase key: {passphrase_key.hex()} ({len(passphrase_key)} bytes)")

        assert(len(passphrase_key) == key_len)
        engine = make_decryptor(passphrase_key, cipher, self.s2k_iv)
        clear_private_data = bytes(engine.update(self.private_data) + engine.finalize())
        
        validate_private_data(clear_private_data, self.s2k_usage)
        LOG.info('Passphrase correct')
        return (self.public_part.getvalue(), clear_private_data)

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
    key = None

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | keyID {self.key_id.hex()} ({lookup_pub_algorithm(self.raw_pub_algorithm)[0]})"

    def decrypt_session_key(self, private_key, private_padding):
        assert( not self.partial )
        pos_start = self.data.tell()
        session_key_version = read_1(self.data)
        if session_key_version != 3:
            raise PGPError(f"Unsupported encrypted session key packet, version {session_key_version}")

        self.key_id = self.data.read(8).hex()
        self.raw_pub_algorithm = read_1(self.data)
        # Remainder is the encrypted key
        self.encrypted_data = get_mpi(self.data)

        key_args = (private_padding, ) if private_padding else ()
        session_data = private_key.decrypt(self.encrypted_data, *key_args)
                
        session_data = io.BytesIO(session_data)
        symalg_id = read_1(session_data)

        name, keylen, symalg = lookup_sym_algorithm(symalg_id)
        symkey = session_data.read(keylen)

        #LOG.debug(f"{name} | {keylen} | Session key: {symkey.hex()}")
        assert( keylen == len(symkey) )
        checksum = read_2(session_data)

        if not sum(symkey) % 65536 == checksum:
            raise PGPError(f"{name} decryption failed")

        return (name, symalg, symkey)


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
        self.version = read_1(self.data)
        assert( self.version == 1 )

        # Do-until.
        data_length, partial = self.length - 1, self.partial
        while True:
            # Produce data
            #LOG.debug(f'Reading data to decrypt: {data_length} bytes - partial {partial}')
            ed = (self.data.read(data_length), data_length, not partial)
            assert( len(ed[0]) == ed[1] )
            decrypted_data = self.engine.send( ed )
            decrypted_data = self._handle_decrypted_data(decrypted_data, not partial)

            # Consume and return data
            yield consumer.send( (decrypted_data, not partial) )

            # More coming?
            if partial:
                data_length, partial = new_tag_length(self.data)
            else:
                break

        # Finally, MDC control
        if self.mdc:
            digest = b'\xD3\x14' + self.hasher.digest() # including prefix, and MDC tag+length
            #LOG.debug(f'digest: {digest.hex().upper()}')
            #LOG.debug(f'   MDC: {self.mdc_value.hex().upper()}')
            if self.mdc_value != digest:
                raise PGPError("MDC Decryption failed")

        #LOG.debug(f'decryption finished')

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
            #LOG.debug(f'PREFIX: {self.prefix.hex()}')
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

        #LOG.debug('Initializing Decompressor')
        is_final_chunk = yield

        algo = read_1(self.data)
        #LOG.debug(f'Compression Algo: {algo}')
        engine = decompressor(algo)

        consumer = consume()
        next(consumer) # start it

        data_length, partial = (self.length - 1 if self.length else None), self.partial

        while True:
            if data_length is not None:
                raise NotImplemented("TODO")

            # Undertermined length
            #LOG.debug('Undertermined length')
            assert( not partial )

            #LOG.debug(f'Reading data to decompress | buffer size {self.data.get_size()}')
            data = self.data.read(data_length)

            #LOG.debug(f'Got some data to decompress: {len(data)}')
            decompressed_data = engine.decompress(data)
            #LOG.debug(f'Decompressed data: {len(decompressed_data)}')
                
            if is_final_chunk:
                #LOG.debug(f'Not more coming: Flushing the decompressor')
                decompressed_data += engine.flush()
                    
            next_is_final_chunk = yield consumer.send( (decompressed_data,is_final_chunk) )
            if is_final_chunk:
                #LOG.debug(f'no more coming: finito | {self.name}')
                break
            is_final_chunk = next_is_final_chunk

        #LOG.debug(f'decompression finished')


class LiteralDataPacket(Packet):

    def process(self):

        #LOG.debug(f'Processing {self.name}')
        is_final_chunk = yield # ready to work

        # TODO: Handle the case where there is not enough data.
        # ie the buffer contains less than filename+6 bytes
        assert( self.data.get_size() > 6 )

        self.data_format = self.data.read(1)
        #LOG.debug(f'data format: {self.data_format.decode()}')

        filename_length = read_1(self.data)
        if filename_length == 0:
            # then sensitive file
            filename = None
        else:
            filename = self.data.read(filename_length)
            assert( len(filename) == filename_length )
            # if filename == '_CONSOLE':
            #     filename = None

        if filename:
            LOG.debug(f'filename: {filename}')

        self.raw_date = read_4(self.data)
        self.date = datetime.utcfromtimestamp(self.raw_date)
        #LOG.debug(f'date: {self.date}')

        #LOG.debug(f'Literal packet length {self.length} | partial {self.partial}')
        data_length, partial = (self.length-6-filename_length if self.length else None), self.partial

        if data_length is None:
            #LOG.debug(f'Undetermined length')
            assert( not partial )

        while True:
            data = self.data.read(data_length)
            #LOG.debug(f'Literal length: {data_length} - partial {partial}')

            data_length = data_length - len(data) if data_length else 0
            if data_length:
                #LOG.debug(f'The body of that packet is not yet complete | Need {data_length} left | {self.name}')
                assert( not is_final_chunk )

            #LOG.debug(f'Got some literal data: {len(data)}')
            next_is_final_chunk = yield data

            if partial:
                new_data_length, new_partial = new_tag_length(self.data)
                data_length += new_data_length
            else:
                if is_final_chunk:
                    break
                is_final_chunk = next_is_final_chunk

        #LOG.debug(f'DONE with {self.name}')

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
    18: SymEncryptedDataPacket,
}
