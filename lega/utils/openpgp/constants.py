from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric import ec

# https://tools.ietf.org/html/rfc4880#section-4.3
tags = {
    0:  "Reserved",
    1:  "Public-Key Encrypted Session Key Packet",
    2:  "Signature Packet",
    3:  "Symmetric-Key Encrypted Session Key Packet",
    4:  "One-Pass Signature Packet",
    5:  "Secret-Key Packet",
    6:  "Public-Key Packet",
    7:  "Secret-Subkey Packet",
    8:  "Compressed Data Packet",
    9:  "Symmetrically Encrypted Data Packet",
    10: "Marker Packet",
    11: "Literal Data Packet",
    12: "Trust Packet",
    13: "User ID Packet",
    14: "Public-Subkey Packet",
    17: "User Attribute Packet",
    18: "Sym. Encrypted and Integrity Protected Data Packet",
    19: "Modification Detection Code Packet",
}

def lookup_tag(tag):
    if tag in (60, 61, 62, 63):
        return "Private or Experimental Values"
    return tags.get(tag, "Unknown")


# Specification: https://tools.ietf.org/html/rfc4880#section-5.2
pub_algorithms = {
    1:  ("RSA Encrypt or Sign", rsa),
    2:  ("RSA Encrypt-Only", rsa),
    3:  ("RSA Sign-Only", rsa),
    #16: ("ElGamal Encrypt-Only", ElGamal),
    17: ("DSA Digital Signature Algorithm", dsa),
    18: ("Elliptic Curve", ec),
    19: ("ECDSA", ec),
    #20: ("Formerly ElGamal Encrypt or Sign", ElGamal),
    #21: ("Diffie-Hellman", None), # future plans
}

def lookup_pub_algorithm(alg):
    if 100 <= alg <= 110:
        return ("Private/Experimental algorithm", None)
    return pub_algorithms.get(alg, ("Unknown", None))


hash_algorithms = {
    1:  "MD5",
    2:  "SHA1",
    3:  "RIPEMD160",
    8:  "SHA256",
    9:  "SHA384",
    10: "SHA512",
    11: "SHA224",
}

def lookup_hash_algorithm(alg):
    # reserved values check
    if alg in (4, 5, 6, 7):
        return "Reserved"
    if 100 <= alg <= 110:
        return "Private/Experimental algorithm"
    return hash_algorithms.get(alg, "Unknown")


sym_algorithms = {
    # (Name, key length, Implementation)
    0:  ("Plaintext or unencrypted", 0, None),
    1:  ("IDEA", 16, algorithms.IDEA),
    2:  ("Triple-DES", 24, algorithms.TripleDES),
    3:  ("CAST5", 16, algorithms.CAST5),
    4:  ("Blowfish", 16, algorithms.Blowfish),
    # 5:  ("Reserved", 8),
    # 6:  ("Reserved", 8),
    7:  ("AES with 128-bit key", 16, algorithms.AES),
    8:  ("AES with 192-bit key", 24, algorithms.AES),
    9:  ("AES with 256-bit key", 32, algorithms.AES),
    #10: ("Twofish with 256-bit key", 32, namedtuple('Twofish256', ['block_size'])(block_size=128)),
    11: ("Camellia with 128-bit key", 16, algorithms.Camellia),
    12: ("Camellia with 192-bit key", 24, algorithms.Camellia),
    13: ("Camellia with 256-bit key", 32, algorithms.Camellia),
}

def lookup_sym_algorithm(alg):
    return sym_algorithms.get(alg, ("Unknown", 0, None))

subpacket_types = {
    2:  "Signature Creation Time",
    3:  "Signature Expiration Time",
    4:  "Exportable Certification",
    5:  "Trust Signature",
    6:  "Regular Expression",
    7:  "Revocable",
    9:  "Key Expiration Time",
    10: "Placeholder for backward compatibility",
    11: "Preferred Symmetric Algorithms",
    12: "Revocation Key",
    16: "Issuer",
    20: "Notation Data",
    21: "Preferred Hash Algorithms",
    22: "Preferred Compression Algorithms",
    23: "Key Server Preferences",
    24: "Preferred Key Server",
    25: "Primary User ID",
    26: "Policy URI",
    27: "Key Flags",
    28: "Signer's User ID",
    29: "Reason for Revocation",
    30: "Features",
    31: "Signature Target",
    32: "Embedded Signature",
}

sig_types = {
    0x00: "Signature of a binary document",
    0x01: "Signature of a canonical text document",
    0x02: "Standalone signature",
    0x10: "Generic certification of a User ID and Public Key packet",
    0x11: "Persona certification of a User ID and Public Key packet",
    0x12: "Casual certification of a User ID and Public Key packet",
    0x13: "Positive certification of a User ID and Public Key packet",
    0x18: "Subkey Binding Signature",
    0x19: "Primary Key Binding Signature",
    0x1f: "Signature directly on a key",
    0x20: "Key revocation signature",
    0x28: "Subkey revocation signature",
    0x30: "Certification revocation signature",
    0x40: "Timestamp signature",
    0x50: "Third-Party Confirmation signature",
}


s2k_types = {
    # (Name, Length)
    0: ("Simple S2K", 2),
    1: ("Salted S2K", 10),
    2: ("Reserved value", 0),
    3: ("Iterated and Salted S2K", 11),
    101: ("GnuPG S2K", 6),
}

def lookup_s2k(s2k_type_id):
    return s2k_types.get(s2k_type_id, ("Unknown", 0))
