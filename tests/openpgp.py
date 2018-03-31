import unittest
import io

from lega.openpgp.packet import iter_packets
from lega.openpgp.utils import make_key, unarmor
from . import openpgp_data

def fetch_private_key(key_id):
    infile = io.BytesIO(bytes.fromhex(openpgp_data.PGP_PRIVKEY_BIN))
    data = None
    for packet in iter_packets(infile):
        if packet.tag == 5:
            data = packet.unlock(openpgp_data.PGP_PASSPHRASE)
        else:
            packet.skip()
    return make_key(data)

def test_session_key():
    '''Check if the session key is correctly decrypted'''
    name = cipher = session_key = None
    output = io.BytesIO()
    infile = io.BytesIO(bytes.fromhex(openpgp_data.ENC_FILE))
    for packet in iter_packets(infile):
        if packet.tag == 1:
            name, cipher, session_key = packet.decrypt_session_key(fetch_private_key)
        else:
            packet.skip()
    
    assert( session_key.hex().upper() == openpgp_data.SESSION_KEY )

def test_decryption():
    '''Decrypt an encrypted file and match with its original'''
    name = cipher = session_key = None
    output = io.BytesIO()
    infile = io.BytesIO(bytes.fromhex(openpgp_data.ENC_FILE))
    for packet in iter_packets(infile):
        if packet.tag == 1:
            name, cipher, session_key = packet.decrypt_session_key(fetch_private_key)
        elif packet.tag == 18:
            for literal_data in packet.process(session_key, cipher):
                output.write(literal_data)
            else:
                packet.skip()
    assert( output.getvalue() == openpgp_data.ORG_FILE )

def test_keyid_for_pubkey():
    '''Get the keyID from armored pub key'''
    infile = io.BytesIO(openpgp_data.PGP_PUBKEY.encode())
    key_id = None
    for packet in iter_packets(unarmor(infile)):
        if packet.tag == 6:
            packet.parse()
            key_id = packet.key_id
        else:
            packet.skip()
    assert( key_id == openpgp_data.KEY_ID )

def test_keyid_for_pubkey_bin():
    '''Get the keyID from binary pub key'''
    infile = io.BytesIO(bytes.fromhex(openpgp_data.PGP_PUBKEY_BIN))
    key_id = None
    for packet in iter_packets(infile):
        if packet.tag == 6:
            packet.parse()
            key_id = packet.key_id
        else:
            packet.skip()
    assert( key_id == openpgp_data.KEY_ID )

def test_keyid_for_privkey():
    '''Get the keyID from armored priv key'''
    infile = io.BytesIO(openpgp_data.PGP_PRIVKEY.encode())
    key_id, data = None, None
    for packet in iter_packets(unarmor(infile)):
        if packet.tag == 5:
            data = packet.unlock(openpgp_data.PGP_PASSPHRASE)
            key_id = packet.key_id
        else:
            packet.skip()
    assert( key_id == openpgp_data.KEY_ID )

def test_keyid_for_privkey_bin():
    '''Get the keyID from binary priv key'''
    infile = io.BytesIO(bytes.fromhex(openpgp_data.PGP_PRIVKEY_BIN))
    key_id, data = None, None
    for packet in iter_packets(infile):
        if packet.tag == 5:
            data = packet.unlock(openpgp_data.PGP_PASSPHRASE)
            key_id = packet.key_id
        else:
            packet.skip()
    assert( key_id == openpgp_data.KEY_ID )

if __name__ == '__main__':
    unittest.main()
