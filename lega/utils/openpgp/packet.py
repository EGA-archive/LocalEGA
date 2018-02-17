from datetime import datetime, timedelta
import hashlib
from math import ceil, log
import io
import binascii
import zlib
import bz2
import logging

from cryptography.hazmat.primitives.asymmetric import padding

from ..exceptions import PGPError
from .constants import lookup_pub_algorithm, lookup_sym_algorithm, lookup_hash_algorithm, lookup_s2k, lookup_tag
from .utils import read_1, read_2, read_4, new_tag_length, old_tag_length, get_mpi, get_int_bytes, bin2hex, unarmor, crc24, derive_key, _decrypt, _decrypt_and_check, make_rsa_key, make_dsa_key, make_elg_key, validate_private_data

LOG = logging.getLogger('openpgp')

class Packet(object):
    '''The base packet object containing various fields pulled from the packet
    header as well as a slice of the packet data.'''
    def __init__(self, tag, new_format, length, pos, cb, outfile):
        self.tag = tag
        self.new_format = new_format
        self.length = length # just for printing
        self.pos = pos
        self.cb = cb
        self.outfile = outfile

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
                data_length, partial = new_tag_length(data)
                self.length += data_length
                data.seek(data_length, io.SEEK_CUR) # skip data
                if not partial:
                    break
        return self

    def __repr__(self):
        return "#{} | tag {:2} | {:5} bytes | pos {:6} | {}".format("new" if self.new_format else "old", self.tag, self.length, self.pos, lookup_tag(self.tag))


class PublicKeyPacket(Packet):

    def parse(self, data, partial):
        assert( not partial )
        pos_start = data.tell()
        self.pubkey_version = read_1(data)
        if self.pubkey_version in (2,3):
            raise PGPError("Warning: version 3 keys are deprecated")
        elif self.pubkey_version != 4:
            raise PGPError(f"Unsupported public key packet, version {self.pubkey_version}")

        self.raw_creation_time = read_4(data)
        self.creation_time = datetime.utcfromtimestamp(self.raw_creation_time)
        # No validity, moved to Signature

        # Parse the key material
        self.raw_pub_algorithm = read_1(data)
        if self.raw_pub_algorithm in (1, 2, 3):
            self.pub_algorithm_type = "rsa"
            # n, e
            self.n = get_mpi(data)
            self.e = get_mpi(data)
            # the length of the modulus in bits
            self.modulus_bitlen = ceil(log(int.from_bytes(self.n,'big'), 2))
        elif self.raw_pub_algorithm == 17:
            self.pub_algorithm_type = "dsa"
            # p, q, g, y
            self.p = get_mpi(data)
            self.q = get_mpi(data)
            self.g = get_mpi(data)
            self.y = get_mpi(data)
        elif self.raw_pub_algorithm in (16, 20):
            self.pub_algorithm_type = "elg"
            # p, g, y
            self.p = get_mpi(data)
            self.q = get_mpi(data)
            self.y = get_mpi(data)
        elif 100 <= self.raw_pub_algorithm <= 110:
            # Private/Experimental algorithms, just move on
            pass
        else:
            raise PGPError(f"Unsupported public key algorithm {self.raw_pub_algorithm}")

        # Hashing only the public part (differs from self.length for private key packets)
        size = data.tell() - pos_start 
        sha1 = hashlib.sha1()
        sha1.update(bytearray( (0x99, (size >> 8) & 0xff, size & 0xff) )) # 0x99 and the 2-octet length
        data.seek(pos_start, io.SEEK_SET) # rewind
        sha1.update(data.read(size))
        self.fingerprint = sha1.hexdigest().upper()
        self.key_id = self.fingerprint[-16:] # lower 64 bits
        return self


    def __repr__(self):
        s = super().__repr__()

        s2 = "Unkown"
        if self.pub_algorithm_type == "rsa":
            s2 = f"RSA\n\t\t* n {bin2hex(self.n)}\n\t\t* e {bin2hex(self.e)}"
        elif self.pub_algorithm_type == "dsa":
            s2 = f"DSA\n\t\t* p {self.p}\n\t\t* q {self.q}\n\t\t* g {self.g}\n\t\t* y {self.y}"
        elif self.pub_algorithm_type == "elg":
            s2 = f"ELG\n\t\t* p {self.p}\n\t\t* g {self.g}\n\t\t* y {self.y}"

        return f"{s}\n\t| {self.creation_time} \n\t| KeyID {self.key_id} (ver 4)({lookup_pub_algorithm(self.raw_pub_algorithm)[0]})\n\t| {s2}"


class SecretKeyPacket(PublicKeyPacket):
    s2k_type_id = None
    s2k_type = None
    s2k_iv = None
    s2k_hash = None
    unlocked = False

    def parse_s2k(self, data):
        self.s2k_type = read_1(data)
        if self.s2k_type == 0:
            # simple string-to-key
            hash_algo = read_1(data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)

        elif self.s2k_type == 1:
            # salted string-to-key
            hash_algo = read_1(data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)
            # 8 bytes salt
            self.s2k_salt = data.read(8)

        elif self.s2k_type == 2:
            # reserved
            pass

        elif self.s2k_type == 3:
            # iterated and salted
            hash_algo = read_1(data)
            self.s2k_hash = lookup_hash_algorithm(hash_algo)
            self.s2k_salt = data.read(8)
            self.s2k_coded_count = read_1(data)
            self.s2k_count = (16 + (self.s2k_coded_count & 15)) << ((self.s2k_coded_count >> 4) + 6)

        elif 100 <= self.s2k_type <= 110:
            raise PGPError("GNU experimental: Not Implemented")
        else:
            raise PGPError(f"Unsupported public key algorithm {self.s2k_type}")

    def parse(self, data, partial):
        assert( not partial )

        # parse the public part
        pos_start = data.tell()
        super().parse(data, partial)

        # parse secret-key packet format from section 5.5.3
        self.s2k_usage = read_1(data)

        if self.s2k_usage == 0:
            # key data not encrypted
            self.s2k_hash = lookup_hash_algorithm("MD5")
            self.parse_private_key_material(data)
            self.checksum = read_2(data)
        elif self.s2k_usage in (254, 255):
            # string-to-key specifier
            self.cipher_id = read_1(data)
            self.s2k_cipher, _, alg = lookup_sym_algorithm(self.cipher_id)
            self.s2k_iv_len = alg.block_size // 8
            self.parse_s2k(data)
            # Get the IV
            self.s2k_iv = data.read(self.s2k_iv_len)

            self.private_data = data.read(self.length + pos_start - data.tell()) # includes 2-bytes checksum or the 20-bytes hash
            self.sha1chk = (self.s2k_usage == 254)
            
        else:
            # it is a symmetric-key encryption algorithm identifier
            self.s2k_cipher, _, alg = lookup_sym_algorithm(self.s2k_usage)
            self.s2k_iv_len = alg.block_size // 8
            # Get the IV
            self.s2k_iv = data.read(self.s2k_iv_len)

        # So, skip to the right place anyway
        data.seek(pos_start + self.length, io.SEEK_SET)
        return self

    def parse_private_key_material(self, data):
        if self.raw_pub_algorithm in (1, 2, 3):
            self.pub_algorithm_type = "rsa"
            # d, p, q, u
            self.d = get_mpi(data)
            self.p = get_mpi(data)
            self.q = get_mpi(data)
            assert( self.p < self.q )
            self.u = get_mpi(data)
        elif self.raw_pub_algorithm == 17:
            self.pub_algorithm_type = "dsa"
            # x
            self.x = get_mpi(data)
        elif self.raw_pub_algorithm in (16, 20):
            self.pub_algorithm_type = "elg"
            # x
            self.x = get_mpi(data)
        elif 100 <= self.raw_pub_algorithm <= 110:
            # Private/Experimental algorithms, just move on
            pass
        else:
            raise PGPError(f"Unsupported public key algorithm {self.raw_pub_algorithm}")

    def unlock(self, passphrase):
        assert( self.s2k_usage )
        if self.unlocked:
            return

        name, key_len, cipher_factory = lookup_sym_algorithm(self.cipher_id)
        iv_len = cipher_factory.block_size // 8
        LOG.debug(f"Unlocking seckey: {name} (keylen: {key_len} bytes) | IV {bin2hex(self.s2k_iv)} ({iv_len} bytes)")
        assert( len(self.s2k_iv) == iv_len )
        passphrase_key = derive_key(passphrase, key_len, self.s2k_type, self.s2k_hash, self.s2k_salt, self.s2k_count)
        LOG.debug(f"derived passphrase key: {bin2hex(passphrase_key)} ({len(passphrase_key)} bytes)")

        assert(len(passphrase_key) == key_len)
        clear_private_data = _decrypt(self.private_data, passphrase_key, cipher_factory, self.s2k_iv)

        validate_private_data(clear_private_data, self.s2k_usage)
        LOG.info('Passphrase correct')
        session_data = io.BytesIO(clear_private_data)
        self.parse_private_key_material(session_data)
        self.unlocked = True

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
                        salt=bin2hex(self.s2k_salt),
                        count=self.s2k_count,
                        coded_count=self.s2k_coded_count)

        return f"{s} \n\t| {s2} \n\t| IV {bin2hex(self.s2k_iv)}"


class UserIDPacket(Packet):
    '''A User ID packet consists of UTF-8 text that is intended to represent
    the name and email address of the key holder. By convention, it includes an
    RFC 2822 mail name-addr, but there are no restrictions on its content.'''
    def parse(self, data, partial):
        assert( not partial )
        self.info = data.read(self.length).decode('utf8')
        return self

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | {self.info}"

class PublicKeyEncryptedSessionKeyPacket(Packet):
    key = None

    def parse(self, data, partial):
        assert( not partial )
        pos_start = data.tell()
        session_key_version = read_1(data)
        if session_key_version != 3:
            raise PGPError(f"Unsupported encrypted session key packet, version {session_key_version}")

        self.key_id = bin2hex(data.read(8))
        self.raw_pub_algorithm = read_1(data)
        # Remainder if the encrypted key
        self.encrypted_m_e_n = get_mpi(data)
        return self

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | keyID {self.key_id.decode()} ({lookup_pub_algorithm(self.raw_pub_algorithm)[0]})"

    def decrypt_session_key(self, private_packet):
        assert( private_packet.raw_pub_algorithm == self.raw_pub_algorithm )

        if not self.key:

            if private_packet.pub_algorithm_type == "rsa":
                self.key, padding = make_rsa_key(int.from_bytes(private_packet.n, "big"),
                                                 int.from_bytes(private_packet.e, "big"),
                                                 int.from_bytes(private_packet.d, "big"),
                                                 int.from_bytes(private_packet.p, "big"),
                                                 int.from_bytes(private_packet.q, "big"),
                                                 int.from_bytes(private_packet.u, "big"))
                args = (padding, )
                
            elif private_packet.pub_algorithm_type == "dsa":
                self.key = make_dsa_key(int.from_bytes(private_packet.y, "big"),
                                        int.from_bytes(private_packet.g, "big"),
                                        int.from_bytes(private_packet.p, "big"),
                                        int.from_bytes(private_packet.q, "big"),
                                        int.from_bytes(private_packet.x, "big"))
                args = ()
                
            elif private_packet.pub_algorithm_type == "elg":
                self.key = make_elg_key(int.from_bytes(private_packet.p, "big"),
                                        int.from_bytes(private_packet.g, "big"),
                                        int.from_bytes(private_packet.y, "big"),
                                        int.from_bytes(private_packet.x, "big"))
                args = ()
            else:
                raise PGPError('Unsupported asymmetric algorithm')

        m_e_n = self.key.decrypt(self.encrypted_m_e_n, *args )
        
        session_data = io.BytesIO(m_e_n)
        symalg_id = read_1(session_data)

        name, keylen, symalg = lookup_sym_algorithm(symalg_id)
        symkey = session_data.read(keylen)

        LOG.debug(f"{name} | {keylen} | Session key: {bin2hex(symkey)}")
        assert( keylen == len(symkey) )
        checksum = read_2(session_data)

        if not sum(symkey) % 65536 == checksum:
            raise PGPError(f"{name} decryption failed")

        return (name, symalg, symkey)


class SymEncryptedDataPacket(Packet):
    mdc = False

    def parse(self, data, partial):
        if self.tag == 18:
            self.mdc = True
        #assert( partial )
        self.version = read_1(data)
        assert( self.version == 1 )
        data.seek(self.length - 1, io.SEEK_CUR)
        LOG.debug(f"-------- length: {self.length}")
        while partial:
            data_length, partial = new_tag_length(data)
            LOG.debug(f"-------- length: {data_length}")
            self.length += data_length
            data.seek(data_length, io.SEEK_CUR) # skip data
        return self

    def __repr__(self):
        s = super().__repr__()
        return f"{s} | version {self.version}"

    # See 5.13 (page 50)
    def decrypt_message(self, f, session_key, cipher):
        LOG.debug(f"============== SESSION KEY: {bin2hex(session_key)}")
        f.seek(self.pos, io.SEEK_SET) # start of packet
        b = read_1(f) 
        data_length, partial = new_tag_length(f) if self.new_format else old_tag_length(f, b & 0x03)
        f.seek(1, io.SEEK_CUR) # skip version
        # data = f.read(data_length-1)
        # yield _decrypt_and_check(data, session_key, cipher, mdc=self.mdc)
        # while partial:
        #     data_length, partial = new_tag_length(f)
        #     data = f.read(data_length)
        #     yield _decrypt_and_check(data, session_key, cipher, mdc=self.mdc)
        data = bytearray(f.read(data_length-1))
        while partial:
            data_length, partial = new_tag_length(f)
            data += bytearray(f.read(data_length))

        plaintext = _decrypt_and_check(bytes(data), session_key, cipher, mdc=self.mdc)
        return self.cb(io.BytesIO(plaintext), self.outfile)

class CompressedDataPacket(Packet):

    def parse(self, data, partial):
        assert( not partial )
        algo = read_1(data)
        d = data.read()
        LOG.debug(f"============== Decompressing {self.length} bytes: {bin2hex(d)}")
        if algo == 0: # Uncompressed
            data = d

        elif algo == 1: # Zip deflate
            data = zlib.decompress(d, -15)

        elif algo == 2: # Zip deflate with zlib header
            data = zlib.decompress(d)

        elif algo == 3: # Bzip2
            data = bz2.decompress(d)
        else:
            raise NotImplementedError()

        return self.cb(io.BytesIO(data), self.outfile)

class LiteralDataPacket(Packet):

    def parse(self, data, partial):
        self.data_format = data.read(1)
        LOG.debug('{:*^30} {}'.format('*',self.data_format.decode()))

        filename_length = read_1(data)
        if filename_length == 0:
            # then sensitive file
            filename = None
        else:
            filename = data.read(filename_length)
            if filename == '_CONSOLE':
                filename = None

        if filename:
            LOG.debug('{:*^30} {}'.format('*',filename))

        self.raw_date = read_4(data)
        self.date = datetime.utcfromtimestamp(self.raw_date)
        LOG.debug('{:*^30} {}'.format('*',self.date))
        
        d = data.read(self.length-6-filename_length)
        LOG.debug('{:*^30} partial {} - {}'.format('*',partial, d.decode()))
        self.outfile.write(d)
        while partial:
            data_length, partial = new_tag_length(data)
            #self.length += data_length
            d = data.read(data_length)
            LOG.debug('{:*^30} partial {} - {}'.format('*',partial, d.decode()))
            self.outfile.write(d)
        return self

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


def parse(data, outfile):
    pos = data.tell()

    # First byte
    b = read_1(data)
    if b is None:
        return None

    #LOG.debug(f"First byte: {b:08b} ({b})")

    # 7th bit of the first byte must be a 1
    if not bool(b & 0x80):
        all = data.read()
        LOG.debug(f'data ({len(all)} bytes): {all}')
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
    packet = PacketType(tag, new_format, data_length, pos, parse, outfile)
    return packet.parse(data, partial)
