import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
from lega.keyserver import routes
from unittest import mock


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
    async def test_retrieve_not_found(self):
        """Retrieve Endpoint not found. In this case PGP key."""
        pgp_resp = await self.client.request("GET", "/retrieve/pgp")
        assert pgp_resp.status == 404


if __name__ == '__main__':
    unittest.main()
