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
    1:  "RSA Encrypt or Sign",
    2:  "RSA Encrypt-Only",
    3:  "RSA Sign-Only",
    16: "ElGamal Encrypt-Only",
    17: "DSA Digital Signature Algorithm",
    18: "Elliptic Curve",
    19: "ECDSA",
    20: "Formerly ElGamal Encrypt or Sign",
    21: "Diffie-Hellman",
}

def lookup_pub_algorithm(alg):
    if 100 <= alg <= 110:
        return "Private/Experimental algorithm"
    return pub_algorithms.get(alg, "Unknown")


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
    # (Name, IV length)
    0:  ("Plaintext or unencrypted", 0),
    1:  ("IDEA", 8),
    2:  ("Triple-DES", 8),
    3:  ("CAST5", 8),
    4:  ("Blowfish", 8),
    5:  ("Reserved", 8),
    6:  ("Reserved", 8),
    7:  ("AES with 128-bit key", 16),
    8:  ("AES with 192-bit key", 16),
    9:  ("AES with 256-bit key", 16),
    10: ("Twofish with 256-bit key", 16),
    11: ("Camellia with 128-bit key", 16),
    12: ("Camellia with 192-bit key", 16),
    13: ("Camellia with 256-bit key", 16),
}

def _lookup_sym_algorithm(alg):
    return sym_algorithms.get(alg, ("Unknown", 0))

def lookup_sym_algorithm(alg):
    return _lookup_sym_algorithm(alg)[0]

def lookup_sym_algorithm_iv_length(alg):
    return _lookup_sym_algorithm(alg)[1]



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
