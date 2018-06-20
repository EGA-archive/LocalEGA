"""
Eureka Discovery for LocalEGA.

* Inspired by https://github.com/wasp/eureka
* Apache 2.0 License https://github.com/wasp/eureka/blob/master/LICENSE
"""
import asyncio
import aiohttp
import logging
import json
import uuid
from functools import wraps


eureka_status = {
    0: 'UP',
    1: 'DOWN',
    2: 'STARTING',
    3: 'OUT_OF_SERVICE',
    4: 'UNKNOWN',
}

LOG = logging.getLogger(__name__)


async def _retry(run, on_failure=None):
    # similar to the rety loop from db.py
    """Main retry loop."""
    nb_try = 5
    try_interval = 20
    LOG.debug(f"{nb_try} attempts (every {try_interval} seconds)")
    count = 0
    backoff = try_interval
    while count < nb_try:
        try:
            return await run()
        except (aiohttp.ClientResponseError,
                aiohttp.ClientError,
                asyncio.TimeoutError) as e:
            LOG.debug(f"Eureka connection error: {e!r}")
            LOG.debug(f"Retrying in {backoff} seconds")
            asyncio.sleep(backoff)
            count += 1
            backoff = (2 ** (count // 10)) * try_interval

    # fail to connect
    if nb_try:
        LOG.debug(f"Eureka server connection fail after {nb_try} attempts ...")
    else:
        LOG.debug("Eureka server attempts was set to 0 ...")

    if on_failure:
        on_failure()


def retry_loop(on_failure=None):
    """Decorator retry something ``try`` times every ``try_interval`` seconds."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async def _process():
                    return await func(*args, **kwargs)
                return await _retry(_process, on_failure=on_failure)
        return wrapper
    return decorator


def _do_exit():
    LOG.error("Could not connect to the Eureka.")
    pass
    # We don't fail right away as we expect the keysever to continue
    # Under "normal deployment" this should exit ?
    # sys.exit(1)


class EurekaRequests:
    """Eureka from Netflix with basic REST operations.

    Following: https://github.com/Netflix/eureka/wiki/Eureka-REST-operations

    .. note:: The eureka url for Spring Framework Eureka is ``http://eureka_host:eureka_port/eureka``
            notice the ``/v2`` is missing and the default port is ``8671``.
    """

    def __init__(self, eureka_url='http://localhost:8761', loop=None):
        """Where we make it happen."""
        self._loop = loop if loop else asyncio.get_event_loop()
        self._eureka_url = eureka_url.rstrip('/') + '/eureka'
        self._headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    @retry_loop(on_failure=_do_exit)
    async def out_of_service(self, app_name, instance_id):
        """Take an instance out of service."""
        url = f'{self._eureka_url}/apps/{app_name}/{instance_id}/status?value={eureka_status[3]}'
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.put(url) as resp:
                return resp.status
                LOG.debug('Eureka out_of_service status response %s' % resp.status)

    async def list_apps(self):
        """Get the apps known to the eureka server."""
        url = f'{self._eureka_url}/apps'
        return await self._get_request(url)

    async def get_by_app(self, app_name):
        """Get an app by its name."""
        app_name = app_name or self._app_name
        url = f'{self._eureka_url}/apps/{app_name}'
        return await self._get_request(url)

    async def get_by_app_instance(self, app_name, instance_id):
        """Get a specific instance, narrowed by app name."""
        app_name = app_name or self._app_name
        instance_id = instance_id or self.instance_id
        url = f'{self._eureka_url}/apps/{app_name}/{instance_id}'
        return await self._get_request(url)

    async def get_by_instance(self, instance_id):
        """Get a specific instance."""
        instance_id = instance_id or self.instance_id
        url = f'{self._eureka_url}/instances/{instance_id}'
        return await self._get_request(url)

    async def get_by_vip(self, vip_address):
        """Query for all instances under a particular vip address."""
        vip_address = vip_address or self._app_name
        url = f'{self._eureka_url}/vips/{vip_address}'
        return await self._get_request(url)

    async def get_by_svip(self, svip_address):
        """Query for all instances under a particular secure vip address."""
        svip_address = svip_address or self._app_name
        url = f'{self._eureka_url}/vips/{svip_address}'
        return await self._get_request(url)

    @retry_loop(on_failure=_do_exit)
    async def _get_request(self, url):
        """General GET request, to simplify things. Expect always JSON as headers set."""
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return await resp.text()


class EurekaClient(EurekaRequests):
    """Eureka Client for registration and deregistration of a client."""

    def __init__(self, app_name, port, ip_addr, hostname,
                 eureka_url, loop,
                 instance_id=None,
                 health_check_url=None,
                 status_check_url=None):
        """Where we make it happen."""
        _default_health = f'http://{ip_addr}:{port}/health'
        EurekaRequests.__init__(self, eureka_url, loop)
        self._app_name = app_name
        self._port = port
        self._hostname = hostname or ip_addr
        self._ip_addr = ip_addr
        self._instance_id = instance_id if instance_id else self._generate_instance_id()
        self._health_check_url = health_check_url if health_check_url else _default_health
        self._status_check_url = status_check_url if status_check_url else self._health_check_url

    @retry_loop(on_failure=_do_exit)
    async def register(self, metadata=None, lease_duration=60, lease_renewal_interval=20):
        """Register application with Eureka."""
        payload = {
            'instance': {
                'instanceId': self._instance_id,
                'leaseInfo': {
                    'durationInSecs': lease_duration,
                    'renewalIntervalInSecs': lease_renewal_interval,
                },
                'port': {
                    '$': self._port,
                    '@enabled': self._port is not None,
                },
                'status': eureka_status[0],
                'hostName': self._hostname,
                'app': self._app_name,
                'ipAddr': self._ip_addr,
                'vipAddress': self._app_name,
                # dataCenterInfo seems to be required
                'dataCenterInfo': {
                    '@class': 'com.netflix.appinfo.MyDataCenterInfo',
                    'name': 'MyOwn',
                },
            }
        }
        if self._health_check_url is not None:
            payload['instance']['healthCheckUrl'] = self._health_check_url
        if self._status_check_url is not None:
            payload['instance']['statusPageUrl'] = self._status_check_url
        if metadata:
            payload['instance']['metadata'] = metadata
        url = f'{self._eureka_url}/apps/{self._app_name}'
        LOG.debug('Registering %s', self._app_name)
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.post(url, data=json.dumps(payload)) as resp:
                return resp.status
                LOG.debug('Eureka register response %s' % resp.status)

    @retry_loop(on_failure=_do_exit)
    async def renew(self):
        """Renew the application's lease."""
        url = f'{self._eureka_url}/apps/{self._app_name}/{self._instance_id}'
        LOG.debug('Renew lease for %s', self._app_name)
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.put(url) as resp:
                return resp.status
                LOG.debug('Eureka renew response %s' % resp.status)

    @retry_loop(on_failure=_do_exit)
    async def deregister(self):
        """Deregister with the remote server, to avoid 500 eror."""
        url = f'{self._eureka_url}/apps/{self._app_name}/{self._instance_id}'
        LOG.debug('Deregister %s', self._app_name)
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.delete(url) as resp:
                return resp.status
                LOG.debug('Eureka deregister response %s' % resp.status)

    @retry_loop(on_failure=_do_exit)
    async def update_metadata(self, key, value):
        """Update metadata of application."""
        url = f'{self._eureka_url}/apps/{self._app_name}/{self._instance_id}/metadata?{key}={value}'
        LOG.debug(f'Update metadata for {self._app_name} instance {self._instance_id}')
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.put(url) as resp:
                return resp.status
                LOG.debug('Eureka update metadata response %s' % resp.status)

    def _generate_instance_id(self):
        """Generate a unique instance id."""
        instance_id = f'{uuid.uuid4()}:{self._app_name}:{self._port}'
        LOG.debug('Generated new instance id: %s for app: %s', instance_id, self._app_name)
        return instance_id
