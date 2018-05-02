import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
from lega.keyserver import routes, Cache, PGPPrivateKey, ReEncryptionKey
import datetime
from . import openpgp_data, rsa_data
# from unittest import mock


class KeyserverTestCase(AioHTTPTestCase):
    """KeyServer

    Testing keyserver by importing the routes and mocking the innerworkings."""

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
    async def test_bad_request(self):
        """Request a key type that does not exist."""
        rsa_resp = await self.client.request("GET", "/active/no_key")
        assert rsa_resp.status == 400

    @unittest_run_loop
    async def test_active_not_found(self):
        """Active Endpoint not found. In this case RSA key."""
        rsa_resp = await self.client.request("GET", "/active/rsa")
        assert rsa_resp.status == 404

    @unittest_run_loop
    async def test_active_private_not_found(self):
        """Active Endpoint private key part not found. In this case RSA key."""
        rsa_resp = await self.client.request("GET", "/active/rsa/private")
        assert rsa_resp.status == 404

    @unittest_run_loop
    async def test_active_public_not_found(self):
        """Active Endpoint public key part not found. In this case RSA key."""
        rsa_resp = await self.client.request("GET", "/active/rsa/public")
        assert rsa_resp.status == 404

    @unittest_run_loop
    async def test_retrieve_not_found(self):
        """Retrieve Endpoint not found. In this case PGP key."""
        pgp_resp = await self.client.request("GET", "/retrieve/pgp/74EACHW8")
        assert pgp_resp.status == 404

    @unittest_run_loop
    async def test_retrieve_public_not_found(self):
        """Retrieve Endpoint public part not found. In this case RSA and PGP keys."""
        rsa_resp = await self.client.request("GET", "/retrieve/rsa/key.1/public")
        pgp_resp = await self.client.request("GET", "/retrieve/pgp/74EACHW8/public")
        assert pgp_resp.status == 404
        assert rsa_resp.status == 404

    @unittest_run_loop
    async def test_retrieve_private_not_found(self):
        """Retrieve Endpoint private part not found. In this case RSA and PGP keys."""
        rsa_resp = await self.client.request("GET", "/retrieve/rsa/key.1/private")
        pgp_resp = await self.client.request("GET", "/retrieve/pgp/74EACHW8/private")
        assert pgp_resp.status == 404
        assert rsa_resp.status == 404


class CacheTestCase(unittest.TestCase):
    """KeyServer Cache

    Testing in memory cache."""

    def setUp(self):
        """Set up cache for testing."""
        self._cache = Cache()

    def test_clear(self):
        """Test clearing Cache."""
        self._cache.set('test_key', 5)
        self._cache.clear()
        self.assertEqual(self._cache.get('test_key'), None)

    def test_key_expired(self):
        """Setting key expired."""
        self._cache.set('test_key', {"value": "key"}, "30/MAR/00 08:00:00")
        print(self._cache.get('test_key'))
        self.assertEqual(self._cache.get('test_key'), None)
        self._cache.clear()

    def test_set_value(self):
        """Retrived cached Value."""
        self._cache.set('test_key', {"value": "key"})
        self.assertEqual(self._cache.get('test_key'), {"value": "key"})
        self._cache.clear()

    def test_check_ttl(self):
        """Check TTL of keys."""
        date_1 = datetime.datetime.strptime(datetime.datetime.now().strftime('%d/%b/%y %H:%M:%S'), "%d/%b/%y %H:%M:%S")
        end_date = date_1 + datetime.timedelta(days=10)
        self._cache.set('test_key', {"value": "key"}, end_date.strftime('%d/%b/%y %H:%M:%S'))
        self._cache.set('expired_key', {"value": "key"}, "30/MAR/00 08:00:00")
        self._cache.set('no_ttl', {"value": "key"}, )
        expected_value = [{"keyID": "test_key", "ttl": '10 days 240 hours 0 minutes 0 seconds'}, {"keyID": "no_ttl", "ttl": "Expiration not set."}]
        self.assertEqual(self._cache.check_ttl(), expected_value)
        self._cache.clear()


class PGPLoadTestCase(unittest.TestCase):
    """KeyServer PGP Key Load

    Testing Loading PGP key."""

    def setUp(self):
        """Set up PGP key."""
        self._infile = 'tests/resources/priv.pgp'
        self._passphrase = openpgp_data.PGP_PASSPHRASE.decode("utf-8")
        self._pgpdata = PGPPrivateKey(self._infile, self._passphrase)

    def test_key_loaded(self):
        """Testing the key data was properly loaded."""
        value = self._pgpdata.load_key()
        self.assertEqual(value, (openpgp_data.KEY_ID, openpgp_data.PGP_PRIVKEY_MATERIAL))


class ReEncryptionLoadTestCase(unittest.TestCase):
    """KeyServer ReEncryption Key Load

    Testing Loading RSA key."""

    def setUp(self):
        """Set up PGP key."""
        self._infile = 'tests/resources/priv.rsa'
        self._passphrase = None  # Not Encrypted
        self._rsadata = ReEncryptionKey(rsa_data.KEY_ID, self._infile, self._passphrase)

    def test_key_loaded(self):
        """Testing the key data was properly loaded."""
        value = self._rsadata.load_key()
        self.assertEqual(value, (rsa_data.KEY_ID, rsa_data.RSA_PRIVKEY_MATERIAL))


if __name__ == '__main__':
    unittest.main()
