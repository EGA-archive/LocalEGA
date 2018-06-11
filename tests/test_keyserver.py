import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
from test.support import EnvironmentVarGuard
from lega.keyserver import routes, Cache
import datetime
from . import pgp_data
import pgpy
from unittest import mock


# class KeyserverTestCase(AioHTTPTestCase):
#     """KeyServer
#
#     Testing keyserver by importing the routes and mocking the innerworkings."""
#
#     async def get_application(self):
#         """Retrieve the routes to a mock server."""
#         app = web.Application()
#         app.router.add_routes(routes)
#         return app
#
#     @unittest_run_loop
#     async def test_health(self):
#         """Simplest test the health endpoint."""
#         resp = await self.client.request("GET", "/health")
#         assert resp.status == 200
#
#     @unittest_run_loop
#     async def test_forbidden(self):
#         """Request a forbidden if type (public/private) that does not exist."""
#         rsa_resp = await self.client.request("GET", "/active/no_key")
#         assert rsa_resp.status == 403
#
#     @unittest_run_loop
#     async def test_bad_request(self):
#         """Request a key type that does not exist."""
#         rsa_resp = await self.client.request("GET", "/active/private")
#         assert rsa_resp.status == 404
#
#     @unittest_run_loop
#     async def test_retrieve_not_found(self):
#         """Retrieve Endpoint not found. In this case PGP key."""
#         pgp_resp = await self.client.request("GET", "/retrieve/pgp/74EACHW8")
#         assert pgp_resp.status == 403
#
#     @unittest_run_loop
#     async def test_retrieve_public_not_found(self):
#         """Retrieve Endpoint public part not found. In this case RSA and PGP keys."""
#         pgp_resp = await self.client.request("GET", "/retrieve/pgp/public")
#         assert pgp_resp.status == 404
#
#     @unittest_run_loop
#     async def test_retrieve_private_not_found(self):
#         """Retrieve Endpoint private part not found. In this case RSA and PGP keys."""
#         pgp_resp = await self.client.request("GET", "/retrieve/pgp/private")
#         assert pgp_resp.status == 404
#
#     @mock.patch('lega.keyserver.check_ttl.check_ttl')
#     @unittest_run_loop
#     async def test_admin_ttl_not_found(self, mock_cache):
#         """Admin ttl bad request."""
#         mock_cache.return_value = []
#         rsa_resp = await self.client.request("GET", "/admin/ttl")
#         print(dir(mock_cache.return_value))
#         assert rsa_resp.status == 400


class CacheTestCase(unittest.TestCase):
    """KeyServer Cache

    Testing in memory cache."""

    def setUp(self):
        """Initialise fixtures."""
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
        date_1 = datetime.datetime.strptime(datetime.datetime.now().strftime('%d/%b/%y %H:%M:%S'), "%d/%b/%y %H:%M:%S")
        expected_value = [{"keyID": "test_key", "ttl": '10 days 240 hours 0 minutes 0 seconds'}]
        with self._key.unlock(pgp_data.PGP_PASSPHRASE) as privkey:
            end_date = date_1 + datetime.timedelta(days=10)
            self._cache.set('test_key', privkey, end_date.strftime('%d/%b/%y %H:%M:%S'))
            self.assertEqual(self._cache.check_ttl(), expected_value)
        self._cache.clear()


if __name__ == '__main__':
    unittest.main()
