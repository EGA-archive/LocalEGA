import unittest
from lega.utils.eureka import EurekaRequests, EurekaClient
import asyncio
import json
from aioresponses import aioresponses
from unittest import mock


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
        assert resp == {}  # For now we don't take into consideration the content

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
        assert resp == {}  # For now we don't take into consideration the content

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
        assert resp == {}  # For now we don't take into consideration the content

    @aioresponses()
    def test_not_found(self, mocked):
        """Get by SVIP."""
        mocked.get(f'{self._eureka_url}/eureka/vips/svipaddress', status=404, body='Not found.')
        resp = self._loop.run_until_complete(self._eurekaconn.get_by_svip('svipaddress'))
        assert resp == "Not found."


class EurekaClientTest(unittest.TestCase):
    """Eureka Client

    Testing Eureka client connection."""

    def setUp(self):
        """Setting things up."""
        self._loop = asyncio.get_event_loop()
        self._eureka_url = 'http://localhost:8761'
        self._port = 5050
        self._host = 'keyserver'
        self._app = 'keyserver'
        self._instance_id = '1N5tAnc3'
        self._eurekaclient = EurekaClient(self._app, port=self._port, ip_addr=self._host,
                                          instance_id=self._instance_id,
                                          eureka_url=self._eureka_url, hostname=self._host,
                                          health_check_url=f'http://{self._host}:{self._port}/health',
                                          loop=self._loop)

    @aioresponses()
    def test_register_app(self, mocked):
        """Add new app to eureka."""
        mocked.post(f'{self._eureka_url}/eureka/apps/{self._app}', status=204)
        resp = self._loop.run_until_complete(self._eurekaclient.register(metadata='data'))
        assert resp == 204

    @aioresponses()
    def test_deregister_app(self, mocked):
        """Deregister app with eureka."""
        mocked.delete(f'{self._eureka_url}/eureka/apps/{self._app}/{self._instance_id}', status=200)
        resp = self._loop.run_until_complete(self._eurekaclient.deregister())
        assert resp == 200

    @aioresponses()
    def test_renew_app(self, mocked):
        """Renew app with eureka."""
        mocked.put(f'{self._eureka_url}/eureka/apps/{self._app}/{self._instance_id}', status=200)
        resp = self._loop.run_until_complete(self._eurekaclient.renew())
        assert resp == 200

    @aioresponses()
    def test_update_metadata(self, mocked):
        """Update app metadata with eureka."""
        key = 'test'
        value = 'value'
        mocked.put(f'{self._eureka_url}/eureka/apps/{self._app}/{self._instance_id}/metadata?{key}={value}', status=200)
        resp = self._loop.run_until_complete(self._eurekaclient.update_metadata('test', 'value'))
        assert resp == 200

    @aioresponses()
    def test_out_of_service(self, mocked):
        """Out of service."""
        mocked.put(f'{self._eureka_url}/eureka/apps/{self._app}/{self._instance_id}/status?value=OUT_OF_SERVICE', status=200)
        resp = self._loop.run_until_complete(self._eurekaclient.out_of_service(self._app, self._instance_id))
        assert resp == 200

    def test_generate_instance_id(self):
        """Generate instance id."""
        instance_id = self._eurekaclient._generate_instance_id()
        assert instance_id.endswith(f':{self._app}:{self._port}')

    @mock.patch('lega.utils.eureka.LOG')
    def test_connection_error(self, mock_logger):
        """Assert connection error."""
        self._loop.run_until_complete(self._eurekaclient.update_metadata('test', 'value'))
        mock_logger.error.assert_called_with("Could not connect to the Eureka.")
