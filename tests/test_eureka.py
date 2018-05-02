import unittest
from lega.utils.eureka import EurekaRequests, EurekaClient
import aiohttp
import asyncio
import json
from aioresponses import aioresponses


class EurekaRequestsTest(unittest.TestCase):
    """Eureka Requests

    Testing Base Eureka connection and requests."""

    def setUp(self):
        """Setting things up."""
        self._loop = asyncio.get_event_loop()
        self._eureka_url = 'http://localhost:8761'
        self._eurekaconn = EurekaRequests(self._eureka_url, self._loop)

    @aioresponses()
    def test_list_apps(self, mocked):
        """List the Apps."""
        mocked.get(f'{self._eureka_url}/eureka/apps', status=200, body=json.dumps({}), content_type='application/json')
        resp = self._loop.run_until_complete(self._eurekaconn.list_apps())
        assert resp == {}  # For now we don't take into consideration the content

    @aioresponses()
    def test_get_app(self, mocked):
        """Get a specific app."""
        mocked.get(f'{self._eureka_url}/eureka/apps/appName', status=200, body=json.dumps({}), content_type='application/json')
        resp = self._loop.run_until_complete(self._eurekaconn.get_by_app('appName'))
        assert resp == {}

    @aioresponses()
    def test_get_by_vip(self, mocked):
        """Get by VIP."""
        mocked.get(f'{self._eureka_url}/eureka/vips/vipaddress', status=200, body=json.dumps({}), content_type='application/json')
        resp = self._loop.run_until_complete(self._eurekaconn.get_by_vip('vipaddress'))
        assert resp == {}  # For now we don't take into consideration the content

    @aioresponses()
    def test_get_app_instance(self, mocked):
        """Get a specific app by instance."""
        mocked.get(f'{self._eureka_url}/eureka/apps/appName/instance1', status=200, body=json.dumps({}), content_type='application/json')
        resp = self._loop.run_until_complete(self._eurekaconn.get_by_app_instance('appName', 'instance1'))
        assert resp == {}

    @aioresponses()
    def test_get_by_instance(self, mocked):
        """Get by instance."""
        mocked.get(f'{self._eureka_url}/eureka/instances/instance2', status=200, body=json.dumps({}), content_type='application/json')
        resp = self._loop.run_until_complete(self._eurekaconn.get_by_instance('instance2'))
        assert resp == {}  # For now we don't take into consideration the content

    @aioresponses()
    def test_get_by_svip(self, mocked):
        """Get by SVIP."""
        mocked.get(f'{self._eureka_url}/eureka/vips/svipaddress', status=200, body=json.dumps({}), content_type='application/json')
        resp = self._loop.run_until_complete(self._eurekaconn.get_by_svip('svipaddress'))
        assert resp == {}


class EurekaClientTest(unittest.TestCase):
    """Eureka Client

    Testing Eureka client connection."""

    def setUp(self):
        """Setting things up."""
        self._loop = asyncio.get_event_loop()
        self._eureka_url = 'http://localhost:8761'
        self._eurekaconn = EurekaClient(self._eureka_url, self._loop)
