'''OpenPGP

Testing that the openpgp utilities with a given set of public/private keys and a simple file to decrypt'''
import unittest
import io
from unittest.mock import patch, MagicMock
from lega.openpgp.packet import iter_packets
from lega.openpgp.generate import generate_pgp_key
from lega.openpgp.utils import make_key, unarmor
from lega.openpgp.__main__ import fetch_private_key
from . import openpgp_data
import json


class PatchContextManager:
    """Following: https://stackoverflow.com/a/32127557 example."""

    def __init__(self, method, enter_return, exit_return=False):
        self._patched = patch(method)
        self._enter_return = enter_return
        self._exit_return = exit_return

    def __enter__(self):
        res = self._patched.__enter__()
        res.context = MagicMock()
        res.context.__enter__.return_value = self._enter_return
        res.context.__exit__.return_value = self._exit_return
        res.return_value = res.context
        return res

    def __exit__(self, type, value, tb):
        return self._patched.__exit__()


@patch('lega.openpgp.__main__.CONF.get')
def test_fetch_from_keyserver(mockedget):
    """Fetch key from keyserver."""
    mockedget.return_value = 'https://ega-keys/retrieve/pgp/%s'
    returned_data = io.BytesIO(json.dumps(openpgp_data.PGP_PRIVKEY_MATERIAL).encode())
    with PatchContextManager('lega.openpgp.__main__.urlopen', returned_data) as mocked:
        fetch_private_key(openpgp_data.KEY_ID)
        mocked.assert_called()  # Just assume the openUrl is called


def util_fetch_private_key(key_id):
    infile = io.BytesIO(bytes.fromhex(openpgp_data.PGP_PRIVKEY_BIN))
    data = None
    for packet in iter_packets(infile):
        if packet.tag == 5:
            data = packet.unlock(openpgp_data.PGP_PASSPHRASE)
        else:
            packet.skip()
    return make_key(data)

def test_session_key():
    '''Retrieve the session key

    Get the session key (Decrypt with PGP Private Key and passphrase).'''
    name = cipher = session_key = None
    output = io.BytesIO()
    infile = io.BytesIO(bytes.fromhex(openpgp_data.ENC_FILE))
    for packet in iter_packets(infile):
        if packet.tag == 1:
            packet.parse()
            name, cipher, session_key = packet.decrypt_session_key(util_fetch_private_key)
        else:
            packet.skip()

    assert( session_key.hex().upper() == openpgp_data.SESSION_KEY )

def test_decryption():
    '''Decrypt an encrypted file and match with its original.'''
    name = cipher = session_key = None
    output = io.BytesIO()
    infile = io.BytesIO(bytes.fromhex(openpgp_data.ENC_FILE))
    for packet in iter_packets(infile):
        if packet.tag == 1:
            packet.parse()
            name, cipher, session_key = packet.decrypt_session_key(util_fetch_private_key)
        elif packet.tag == 18:
            for literal_data in packet.process(session_key, cipher):
                output.write(literal_data)
            else:
                packet.skip()
    assert( output.getvalue() == openpgp_data.ORG_FILE )

def test_keyid_for_pubkey():
    '''Get the keyID from armored pub key.'''
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
    '''Get the keyID from binary pub key.'''
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
    '''Get the keyID from armored priv key.'''
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
    '''Get the keyID from binary priv key.'''
    infile = io.BytesIO(bytes.fromhex(openpgp_data.PGP_PRIVKEY_BIN))
    key_id, data = None, None
    for packet in iter_packets(infile):
        if packet.tag == 5:
            data = packet.unlock(openpgp_data.PGP_PASSPHRASE)
            key_id = packet.key_id
        else:
            packet.skip()
    assert( key_id == openpgp_data.KEY_ID )

def test_generate_pgp():
    """Test generation of PGP armored key tuple."""
    key_pair = generate_pgp_key("name", "example@example.com", "No comment.")
    # Testing that it generates a tuple
    assert isinstance(key_pair, tuple)
    # Testing the armored structure
    assert key_pair[0].startswith('-----BEGIN PGP PUBLIC KEY BLOCK-----\n')
    assert key_pair[1].startswith('-----BEGIN PGP PRIVATE KEY BLOCK-----\n')


if __name__ == '__main__':
    unittest.main()
