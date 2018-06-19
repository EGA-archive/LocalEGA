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


class KeyserverTestCase(AioHTTPTestCase):
    """KeyServer

    Testing keyserver by importing the routes and mocking the innerworkings."""

    env = EnvironmentVarGuard()
    env.set('LEGA_PASSWORD', 'value')
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
        self._key, _ = pgpy.PGPKey.from_blob(pgp_data.PGP_PRIVKEY)
        with self.env:
            self._cache = Cache()

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('LEGA_PASSWORD')

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
        expected_value = [{"keyID": "test_key",
                           "ttl": f"{tdelta.days} days {tdelta.days * 24 + tdelta.seconds // 3600} hours {(tdelta.seconds % 3600) // 60} minutes {tdelta.seconds} seconds"}]
        self.assertEqual(self._cache.check_ttl(), expected_value)
        self._cache.clear()


class TestBasicFunctionsKeyserver(unittest.TestCase):
    """Keyserver Base

    Testing basic functions from keyserver."""

    def setUp(self):
        """Initialise fixtures."""
        self.env = EnvironmentVarGuard()
        self.env.set('LEGA_PASSWORD', 'value')

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('LEGA_PASSWORD')

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

    @mock.patch('lega.keyserver.ssl')
    @mock.patch('lega.keyserver.web')
    @mock.patch('lega.keyserver.asyncio')
    def test_load_args(self, mock_async, mock_webapp, mock_ssl):
        """Should start the webapp, with a configuration and fake key list."""
        main(['--keys', '/keys/list'])
        mock_webapp.run_app.assert_called()


if __name__ == '__main__':
    unittest.main()
