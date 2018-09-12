import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
from test.support import EnvironmentVarGuard
from lega.keyserver import routes, Cache, _unlock_key, main, load_keys_conf
import datetime
from . import pgp_data
import pgpy
from unittest import mock
from testfixtures import tempdir
import os
from hashlib import md5

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes)


def EVP_ByteToKey(pwd, md, salt, key_len, iv_len):
    buf = md(pwd + salt).digest()
    d = buf
    while len(buf) < (iv_len + key_len):
        d = md(d + pwd + salt).digest()
        buf += d
    return buf[:key_len], buf[key_len:key_len + iv_len]


def aes_encrypt(pwd, ptext, md):
    key_len, iv_len = 32, 16

    # generate salt
    salt = os.urandom(8)

    # generate key, iv from password
    key, iv = EVP_ByteToKey(pwd, md, salt, key_len, iv_len)

    # pad plaintext
    pad = padding.PKCS7(128).padder()
    ptext = pad.update(ptext) + pad.finalize()

    # create an encryptor
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # encrypt plain text
    ctext = encryptor.update(ptext) + encryptor.finalize()
    ctext = b'Salted__' + salt + ctext

    # encode base64
    return ctext


class KeyserverTestCase(AioHTTPTestCase):
    """KeyServer

    Testing keyserver by importing the routes and mocking the innerworkings."""

    env = EnvironmentVarGuard()
    env.set('LEGA_PASSWORD', 'value')
    env.set('KEYS_PASSWORD', 'value')
    with env:
        _cache = Cache()

    async def get_application(self):
        """Retrieve the routes to a mock server."""
        app = web.Application()
        app.router.add_routes(routes)
        return app

    @unittest_run_loop
    async def test_health(self):
        """Simplest test the health endpoint."""
        resp = await self.client.request("GET", "/health")
        assert resp.status == 200

    @unittest_run_loop
    async def test_forbidden(self):
        """Request a forbidden if type (public/private) that does not exist."""
        rsa_resp = await self.client.request("GET", "/active/no_key")
        assert rsa_resp.status == 403

    @unittest_run_loop
    async def test_bad_request(self):
        """Request a key type that does not exist."""
        rsa_resp = await self.client.request("GET", "/active/private")
        assert rsa_resp.status == 404

    @unittest_run_loop
    async def test_retrieve_not_found(self):
        """Retrieve Endpoint not found. In this case PGP key."""
        pgp_resp = await self.client.request("GET", "/retrieve/pgp/74EACHW8")
        assert pgp_resp.status == 403


class CacheTestCase(unittest.TestCase):
    """KeyServer Cache

    Testing in memory cache."""

    def setUp(self):
        """Initialise fixtures."""
        self.FMT = '%d/%b/%y %H:%M:%S'
        self.env = EnvironmentVarGuard()
        self.env.set('LEGA_PASSWORD', 'value')
        self.env.set('KEYS_PASSWORD', 'value')
        self._key, _ = pgpy.PGPKey.from_blob(pgp_data.PGP_PRIVKEY)
        with self.env:
            self._cache = Cache()

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('LEGA_PASSWORD')
        self.env.unset('KEYS_PASSWORD')

    def test_clear(self):
        """Test clearing Cache, should return empty cache."""
        with self._key.unlock(pgp_data.PGP_PASSPHRASE) as privkey:
            self._cache.set('test_key', privkey)
        self._cache.clear()
        self.assertEqual(self._cache.get('test_key', 'private'), None)

    def test_key_expired(self):
        """Setting key expired, should make key invisible in cache."""
        with self._key.unlock(pgp_data.PGP_PASSPHRASE) as privkey:
            self._cache.set('test_key', privkey, "30/MAR/00 08:00:00")
        self.assertEqual(self._cache.get('test_key', 'private'), None)
        self._cache.clear()

    def test_set_value(self):
        """Retrived cached Value, should return the proper cached value."""
        with self._key.unlock(pgp_data.PGP_PASSPHRASE) as privkey:
            self._cache.set('test_key', privkey)
        self.assertEqual(self._cache.get('test_key', 'public').hex(), pgp_data.PGP_PUBKEY_BIN)
        self._cache.clear()

    def test_check_ttl(self):
        """Check TTL of keys, should return a value."""
        date_1 = datetime.datetime.strptime(datetime.datetime.now().strftime(self.FMT), self.FMT)
        end_date = date_1 + datetime.timedelta(days=10)
        with self._key.unlock(pgp_data.PGP_PASSPHRASE) as privkey:
            self._cache.set('test_key', privkey, end_date.strftime('%d/%b/%y %H:%M:%S'))

        today = datetime.datetime.today().strftime(self.FMT)
        tdelta = end_date - datetime.datetime.strptime(today, self.FMT)
        tdelta = datetime.timedelta(days=tdelta.days, seconds=tdelta.seconds)

        days = tdelta.days
        hours = tdelta.days * 24 + tdelta.seconds // 3600
        minutes = tdelta.seconds % 3600 // 60
        seconds = tdelta.seconds

        expected_value = [{"keyID": "test_key",
                           "ttl": f"{days} days {hours} hours {minutes} minutes {seconds} seconds"}]
        self.assertEqual(self._cache.check_ttl(), expected_value)
        self._cache.clear()


class TestBasicFunctionsKeyserver(unittest.TestCase):
    """Keyserver Base

    Testing basic functions from keyserver."""

    def setUp(self):
        """Initialise fixtures."""
        self.env = EnvironmentVarGuard()
        self.env.set('LEGA_PASSWORD', 'value')
        self.env.set('KEYS_PASSWORD', 'value')

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('LEGA_PASSWORD')
        self.env.unset('KEYS_PASSWORD')

    @tempdir()
    @mock.patch('lega.keyserver._cache')
    def test_unlock_key_public_error(self, mock_cache, filedir):
        """Trying to unlock public key should return assertion error."""
        pub_keyfile = filedir.write('pub_key.asc', pgp_data.PGP_PUBKEY.encode('utf-8'))
        with self.env:
            mock_cache.return_value = Cache()
        with self.assertRaises(AssertionError):
            _unlock_key(pgp_data.PGP_NAME, path=pub_keyfile)
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.keyserver._active')
    @mock.patch('lega.keyserver._cache')
    def test_unlock_key_private(self, mock_cache, mock_active, filedir):
        """Trying to unlock private key."""
        pub_keyfile = filedir.write('pub_key.asc', pgp_data.PGP_PRIVKEY.encode('utf-8'))
        with self.env:
            mock_cache.return_value = Cache()
        _unlock_key(pgp_data.PGP_NAME, path=pub_keyfile, passphrase=pgp_data.PGP_PASSPHRASE)
        mock_cache.set.assert_called()
        filedir.cleanup()

    @mock.patch('lega.keyserver._unlock_key')
    def test_load_keys_conf(self, mock_unlock):
        """Testing loading keys configuration."""
        data = mock.MagicMock(name='sections')
        data.sections.return_value = ['Section']
        load_keys_conf(data)
        mock_unlock.assert_called()

    @tempdir()
    @mock.patch('lega.keyserver.ssl')
    @mock.patch('lega.keyserver.web')
    @mock.patch('lega.keyserver.asyncio')
    def test_load_args_unec_file(self, mock_async, mock_webapp, mock_ssl, filedir):
        """Should start the webapp, with a configuration and fake key list from unecrypted file."""
        fake_config = """[DEFAULT]
        active : key.1

        [key.1]
        path : /etc/ega/pgp/ega.sec
        passphrase : smth
        expire: 30/MAR/19 08:00:00"""
        conf_file = filedir.write('list.smth', fake_config.encode('utf-8'))
        main(['--keys', conf_file])
        mock_webapp.run_app.assert_called()
        filedir.cleanup()

    @mock.patch('lega.keyserver.ssl')
    @mock.patch('lega.keyserver.web')
    @mock.patch('lega.keyserver.asyncio')
    def test_file_not_found(self, mock_async, mock_webapp, mock_ssl):
        """Should raise file not found, unecrypted file."""
        with self.assertRaises(FileNotFoundError):
            main(['--keys', '/keys/somefile.smth'])

    # TO DO Use to encrypthttps://www.pythonsheets.com/notes/python-crypto.html#aes-cbc-mode-encrypt-via-password-using-cryptography

    @tempdir()
    @mock.patch('lega.keyserver.ssl')
    @mock.patch('lega.keyserver.web')
    @mock.patch('lega.keyserver.asyncio')
    def test_load_args_enc_file(self, mock_async, mock_webapp, mock_ssl, filedir):
        """Should start the webapp, with a configuration and fake key list encrypted config file."""
        # We are not encrypting this but it is faked
        # to make things accuratw we should encrypt it
        fake_config = """[DEFAULT]
        active : key.1

        [key.1]
        path : /etc/ega/pgp/ega.sec
        passphrase : smth
        expire: 30/MAR/19 08:00:00"""
        result = aes_encrypt(b'value', fake_config.encode('utf-8'), md5)
        conf_file = filedir.write('list.enc', result)
        with self.env:
            main(['--keys', conf_file])
            mock_webapp.run_app.assert_called()
        filedir.cleanup()

    @mock.patch('lega.keyserver.ssl')
    @mock.patch('lega.keyserver.web')
    @mock.patch('lega.keyserver.asyncio')
    def test_file_not_found_enc(self, mock_async, mock_webapp, mock_ssl):
        """Should raise file not found, even if suffix is different than *.enc."""
        with self.assertRaises(FileNotFoundError):
            main(['--keys', '/keys/somefile.enc'])


if __name__ == '__main__':
    unittest.main()
