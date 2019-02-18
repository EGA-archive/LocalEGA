import os
import configparser
from pathlib import Path
from hashlib import md5


from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes)

# Based on
# https://www.pythonsheets.com/notes/python-crypto.html#aes-cbc-mode-decrypt-via-password-using-cryptography
# Provided under MIT license: https://github.com/crazyguitar/pysheeet/blob/master/LICENSE


def EVP_ByteToKey(pwd, md, salt, key_len, iv_len):
    """Derive key and IV.

    Based on https://www.openssl.org/docs/man1.0.2/crypto/EVP_BytesToKey.html
    """
    buf = md(pwd + salt).digest()
    d = buf
    while len(buf) < (iv_len + key_len):
        d = md(d + pwd + salt).digest()
        buf += d
    return buf[:key_len], buf[key_len:key_len + iv_len]


def aes_decrypt(pwd, ctext, md, encoding='utf-8'):
    """Decrypt AES."""
    assert pwd, "You must supply a password as the first argument"

    # check magic
    if ctext[:8] != b'Salted__':
        raise ValueError("bad magic number")

    # get salt
    salt = ctext[8:16]

    # generate key, iv from password
    key, iv = EVP_ByteToKey(pwd, md, salt, 32, 16)

    # decrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    ptext = decryptor.update(ctext[16:]) + decryptor.finalize()

    # unpad plaintext
    unpadder = padding.PKCS7(128).unpadder()  # 128 bit
    ptext = unpadder.update(ptext) + unpadder.finalize()
    return ptext.decode(encoding)


class KeysConfiguration(configparser.ConfigParser):
    """Parse keyserver configuration."""

    def __init__(self, args=None, encoding='utf-8'):
        """Load a configuration file from `args`."""
        super().__init__()
        # Finding the --keys file. Raise Error otherwise
        filepath = Path(args[args.index('--keys') + 1]).expanduser()

        if filepath.suffix != '.enc':
            conf = filepath.open(encoding=encoding).read()
        else:
            assert 'KEYS_PASSWORD' in os.environ, "KEYS_PASSWORD must be defined as an environment variable"
            with open(filepath, "rb") as f:
                conf = aes_decrypt(os.environ.get('KEYS_PASSWORD', None).encode(), f.read(), md5, encoding=encoding)

        self.read_string(conf, source=str(filepath))
