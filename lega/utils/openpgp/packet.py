from datetime import datetime, timedelta
import hashlib
from math import ceil, log
import io
import binascii

from Crypto.PublicKey import RSA

from ..exceptions import PGPError
from .utils import read_1, read_2, read_4, new_tag_length, old_tag_length, get_mpi, get_int_bytes, get_key_id, unarmor, crc24
from .constants import lookup_pub_algorithm, lookup_sym_algorithm, lookup_sym_algorithm_iv_length, lookup_hash_algorithm, lookup_s2k, lookup_tag

DEBUG = False
def debug():
    global DEBUG
    DEBUG = True

class Packet(object):
    '''The base packet object containing various fields pulled from the packet
    header as well as a slice of the packet data.'''
    def __init__(self, tag, new_format, length, pos):
        self.tag = tag
        self.new_format = new_format
        self.length = length
        self.pos = pos

    def parse(self, data, partial):
        '''Perform any parsing necessary to populate fields on this packet.
        This method is called as the last step in __init__(). The base class
        method is a no-op; subclasses should use this as required.'''
        self.partial = partial
        if not self.partial:
            data.seek(self.length, io.SEEK_CUR) # skip data
        else:
            data.seek(self.length, io.SEEK_CUR) # skip data
            while True:
                data_length, partial,_ = new_tag_length(data)
                self.length += data_length
                data.seek(data_length, io.SEEK_CUR) # skip data
                if not partial:
                    break

    def __repr__(self):
        if DEBUG:
            return "#{} | tag {:2} | {:5} bytes | pos {:6} | {}".format("new" if self.new_format else "old", self.tag, self.length, self.pos, lookup_tag(self.tag))
        return "tag {:2} | {}".format(self.tag, lookup_tag(self.tag))


class PublicKeyPacket(Packet):

    def parse(self, data, partial):
        assert( not partial )
        self.pubkey_version = read_1(data)
        if self.pubkey_version in (2, 3):
            self.raw_creation_time = read_4(data)
            self.creation_time = datetime.utcfromtimestamp(self.raw_creation_time)

            self.raw_days_valid = read_2(data)
            if self.raw_days_valid > 0:
                self.expiration_time = self.creation_time + timedelta(days=self.raw_days_valid)

            self.parse_key_material(data)
            md5 = hashlib.md5()
            # Key type must be RSA for v2 and v3 public keys
            if self.pub_algorithm_type == "rsa":
                key_id = ('%X' % self.modulus)[-8:].zfill(8)
                self.key_id = key_id.encode('ascii')
                md5.update(get_int_bytes(self.modulus))
                md5.update(get_int_bytes(self.exponent))
            elif self.pub_algorithm_type == "elg":
                # Of course, there are ELG keys in the wild too. This formula
                # for calculating key_id and fingerprint is derived from an old
                # key and there is a test case based on it.
                key_id = ('%X' % self.prime)[-8:].zfill(8)
                self.key_id = key_id.encode('ascii')
                md5.update(get_int_bytes(self.prime))
                md5.update(get_int_bytes(self.group_gen))
            else:
                raise PGPError(f"Invalid non-RSA v{self.pubkey_version} public key")
            self.fingerprint = md5.hexdigest().upper().encode('ascii')
        elif self.pubkey_version == 4:
            sha1 = hashlib.sha1()
            seed_bytes = (0x99, (self.length >> 8) & 0xff, self.length & 0xff)
            sha1.update(bytearray(seed_bytes))
            sha1.update(data.read(self.length-1))
            self.fingerprint = sha1.hexdigest().upper().encode('ascii')
            self.key_id = self.fingerprint[24:]

            self.raw_creation_time = read_4(data)
            self.creation_time = datetime.utcfromtimestamp(self.raw_creation_time)

            self.parse_key_material(data)
        else:
            raise PGPError(f"Unsupported public key packet, version {self.pubkey_version}")

    def parse_key_material(self, data):
        self.raw_pub_algorithm = read_1(data)
        if self.raw_pub_algorithm in (1, 2, 3):
            self.pub_algorithm_type = "rsa"
            # n, e
            self.modulus = get_mpi(data)
            self.exponent = get_mpi(data)
            # the length of the modulus in bits
            self.modulus_bitlen = int(ceil(log(self.modulus, 2)))
        elif self.raw_pub_algorithm == 17:
            self.pub_algorithm_type = "dsa"
            # p, q, g, y
            self.prime = get_mpi(data)
            self.group_order = get_mpi(data)
            self.group_gen = get_mpi(data)
            self.key_value = get_mpi(data)
        elif self.raw_pub_algorithm in (16, 20):
            self.pub_algorithm_type = "elg"
            # p, g, y
            self.prime = get_mpi(data)
            self.group_gen = get_mpi(data)
            self.key_value = get_mpi(data)
        elif 100 <= self.raw_pub_algorithm <= 110:
            # Private/Experimental algorithms, just move on
            pass
        else:
            raise PGPError(f"Unsupported public key algorithm {self.raw_pub_algorithm}")


    def __repr__(self):
        s = super().__repr__()
        return f"{s} | Keyid Ox{self.key_id.decode('ascii')} | {lookup_pub_algorithm(self.raw_pub_algorithm)}"


class SecretKeyPacket(PublicKeyPacket):

    def parse(self, data, partial):
        # parse the public part
        super(SecretKeyPacket, self).parse(data, partial)

        # parse secret-key packet format from section 5.5.3
        self.s2k_id = read_1(data)

        if self.s2k_id == 0:
            # plaintext key data
            self.parse_private_key_material(data)
            self.checksum = read_2(data)
        elif self.s2k_id in (254, 255):
            # encrypted key data
            cipher_id = read_1(data)
            self.s2k_cipher = lookup_sym_algorithm(cipher_id)

            # s2k_length is the len of the entire S2K specifier, as per
            # section 3.7.1 in RFC 4880
            # we parse the info inside the specifier, but verify the # of
            # octects we've parsed matches the expected length of the s2k
            s2k_type_id = read_1(data)
            name, s2k_length = lookup_s2k(s2k_type_id)
            self.s2k_type = name

            has_iv = True
            if s2k_type_id == 0:
                # simple string-to-key
                hash_id = read_1(data)
                self.s2k_hash = lookup_hash_algorithm(hash_id)

            elif s2k_type_id == 1:
                # salted string-to-key
                hash_id = read_1(data)
                self.s2k_hash = lookup_hash_algorithm(hash_id)
                # ignore 8 bytes
                data.seek(8, io.SEEK_CUR)

            elif s2k_type_id == 2:
                # reserved
                pass

            elif s2k_type_id == 3:
                # iterated and salted
                hash_id = read_1(data)
                self.s2k_hash = lookup_hash_algorithm(hash_id)
                # ignore 8 bytes + ignore count
                data.seek(9, io.SEEK_CUR)
                # TODO: parse and store count ?

            elif 100 <= s2k_type_id <= 110:
                raise PGPError("GNU experimental: Not Implemented")
            else:
                raise PGPError(f"Unsupported public key algorithm {s2k_type_id}")

            if has_iv:
                s2k_iv_len = lookup_sym_algorithm_iv_length(cipher_id)
                self.s2k_iv = get_key_id(data.read(s2k_iv_len))

            # TODO decrypt key data
            # TODO parse checksum

    def parse_private_key_material(self, data):
        if self.raw_pub_algorithm in (1, 2, 3):
            self.pub_algorithm_type = "rsa"
            # d, p, q, u
            self.exponent_d = get_mpi(data)
            self.prime_p = get_mpi(data)
            self.prime_q = get_mpi(data)
            self.multiplicative_inverse = get_mpi(data)
        elif self.raw_pub_algorithm == 17:
            self.pub_algorithm_type = "dsa"
            # x
            self.exponent_x = get_mpi(data)
        elif self.raw_pub_algorithm in (16, 20):
            self.pub_algorithm_type = "elg"
            # x
            self.exponent_x = get_mpi(data)
        elif 100 <= self.raw_pub_algorithm <= 110:
            # Private/Experimental algorithms, just move on
            pass
        else:
            raise PGPError(f"Unsupported public key algorithm {self.raw_pub_algorithm}")

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | S2K {self.s2k_id} | S2K cipher {self.s2k_cipher} | S2K type {self.s2k_type} | IV {self.s2k_iv}"


class UserIDPacket(Packet):
    '''A User ID packet consists of UTF-8 text that is intended to represent
    the name and email address of the key holder. By convention, it includes an
    RFC 2822 mail name-addr, but there are no restrictions on its content.'''
    def parse(self, data, partial):
        assert( not partial )
        self.info = data.read(self.length).decode('utf8')

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | {self.info}"

class PublicKeyEncryptedSessionKeyPacket(Packet):
    def parse(self, data, partial):
        session_key_version = read_1(data)
        if session_key_version != 3:
            raise PGPError(f"Unsupported encrypted session key packet, version {session_key_version}")

        self.key_id = get_key_id(data.read(8))
        self.raw_pub_algorithm = read_1(data)
        # Remainder if the encrypted key
        self.encrypted_session_key = data.read(self.length-10)

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | keyID {self.key_id.decode()} ({lookup_pub_algorithm(self.raw_pub_algorithm)})"

class SymEncryptedDataPacket(Packet):

    def parse(self, data, partial):
        assert( partial )
        self.version = read_1(data)
        assert( self.version == 1 )
        data.seek(self.length-1, io.SEEK_CUR)
        while True:
            data_length, partial,_ = new_tag_length(data)
            self.length += data_length
            data.seek(data_length, io.SEEK_CUR) # skip data
            if not partial:
                break

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | version {self.version}"


PACKET_TYPES = {
    1:  PublicKeyEncryptedSessionKeyPacket,
    # # # 2:  SignaturePacket,
    # 5:  SecretKeyPacket,
    # 6:  PublicKeyPacket,
    # 7:  SecretKeyPacket,
    # # 9:  SymEncryptedDataPacket,
    # # 12: TrustPacket,
    13: UserIDPacket,
    # 14: PublicKeyPacket,
    # # # 17: UserAttributePacket,
    18: SymEncryptedDataPacket,
}


def parse(data):
    '''Returns a Packet object constructed from 'data' at its current position.
    Returns None if EOF for data'''

    pos = data.tell()

    # First byte
    b = read_1(data)
    if b is None:
        return None

    #print(f"First byte: {b:08b} ({b})")

    # 7th bit of the first byte must be a 1
    if not bool(b & 0x80):
        all = data.read()
        print(f'data ({len(all)} bytes): {all}')
        raise PGPError("incorrect packet header")

    # the header is in new format if bit 6 is set
    new_format = bool(b & 0x40)

    # tag encoded in bits 5-0 (new packet format)
    tag = b & 0x3f

    if new_format:
        # length is encoded in the second (and following) octet
        data_length, partial,_ = new_tag_length(data)
    else:
        tag >>= 2 # tag encoded in bits 5-2, discard bits 1-0
        length_type = b & 0x03 # get the last 2 bits
        data_length, partial = old_tag_length(data, length_type)

    PacketType = PACKET_TYPES.get(tag, Packet)
    packet = PacketType(tag, new_format, data_length, pos)
    packet.parse(data, partial)
    return packet
