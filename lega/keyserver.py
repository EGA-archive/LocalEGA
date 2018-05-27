#!/usr/bin/env python3

'''\
The Keyserver provides a REST endpoint for retrieving PGP and Re-encryption keys.
The keyserver also registers with Eureka service discovery.
'''


import sys
import asyncio
from aiohttp import web
import logging
import time
import datetime
from pathlib import Path
import ssl
import struct

from .conf import CONF, KeysConfiguration
from .utils import get_file_content, db
from .utils.eureka import EurekaClient

LOG = logging.getLogger('keyserver')
routes = web.RouteTableDef()

class Cache:
    """In memory cache."""

    def __init__(self, max_size=10, ttl=None):
        """Initialise cache."""
        self._store = dict()
        self._max_size = max_size
        self._ttl = ttl
        self._FMT = '%d/%b/%y %H:%M:%S'

    def set(self, key, value, ttl=None):
        """Assign in the store to the the key the value, its ttl."""
        self._check_limit()
        ttl = self._ttl if not ttl else self._parse_date_time(ttl)
        self._store[key] = (value, ttl)

    def get(self, key):
        """Retrieve value based on key."""
        data = self._store.get(key)
        if not data:
            return None
        else:
            value, expire = data
            if expire and time.time() > expire:
                del self._store[key]
                return None
            return value

    def check_ttl(self):
        """Check ttl for all keys."""
        keys = []
        for key, data in self._store.items():
            value, expire = data
            if expire and time.time() < expire:
                keys.append({"keyID": key, "ttl": self._time_delta(expire)})
            if expire is None:
                keys.append({"keyID": key, "ttl": "Expiration not set."})
        return keys

    def _time_delta(self, expire):
        """"Convert time left in human readable format."""
        # A lot of back and forth transformation
        end_time = datetime.datetime.fromtimestamp(expire).strftime(self._FMT)
        today = datetime.datetime.today().strftime(self._FMT)
        tdelta = datetime.datetime.strptime(end_time, self._FMT) - datetime.datetime.strptime(today, self._FMT)

        if tdelta.days > 0:
            tdelta = datetime.timedelta(days=tdelta.days, seconds=tdelta.seconds)
            return f"{tdelta.days} days {tdelta.days * 24 + tdelta.seconds // 3600} hours {(tdelta.seconds % 3600) // 60} minutes {tdelta.seconds} seconds"

    def _parse_date_time(self, date_time):
        """We allow ttl to be specified by date and time.

        Example of set time and date 30/MAR/18 08:00:00 .
        """
        return time.mktime(datetime.datetime.strptime(date_time, self._FMT).timetuple())

    def _check_limit(self):
        """Check if current cache size exceeds maximum cache size and pop the oldest item in this case."""
        if len(self._store) >= self._max_size:
            self._store.popitem(last=False)

    def clear(self):
        """Clear all cache."""
        self._store = dict()


_cache = Cache() # keys are uppercase
_active = None

####################################
# Caching the keys
####################################

async def activate_key(data):
    """(Re)Activate a key."""
    key, _ = pgpy.PGPKey.from_file(data.get('path'))
    with key.unlock(data.get('passphrase')) as k:
        key_id = k.fingerprint.keyid.upper()
        LOG.debug(f'Activating key: {key_id}')
        _cache.set(key_id, k, ttl=data.get('expire', None))

####################################
# Retrieve the active keys
####################################

@routes.get('/active/{key_type}')
async def retrieve_active_key(request):
    key_type = request.match_info['key_type'].lower()
    LOG.debug(f'Requesting active ({key_type}) key')
    k = _cache.get(_active)
    if k:
        value = k.pubkey if key_type == 'public' else k
        return web.json_response(bytes(value))
    else:
        LOG.warn(f"Requested active ({key_type}) key not found.")
        return web.HTTPNotFound()

@routes.get('/retrieve/{key_type}/{requested_id}')
async def retrieve_key(request):
    requested_id = request.match_info['requested_id']
    key_type = request.match_info['key_type'].lower()
    key_id = requested_id[-16:].upper()
    LOG.debug(f'Requested {key_type.upper()} key with ID {requested_id}')
    k = _cache.get(key_id)
    if k:
        value = k.pubkey if key_type == 'public' else k
        return web.json_response(value)
    else:
        LOG.warn(f"Requested key {requested_id} not found.")
        return web.HTTPNotFound()

@routes.post('/admin/unlock')
async def unlock_key(request):
    """Unlock a key via a POST request.
    POST request takes the form:
    \{"type": "pgp", "private": "path/to/file.sec", "passphrase": "pass", "expire": "30/MAR/18 08:00:00"\}
    """
    key_info = await request.json()
    LOG.debug(f'Admin unlocking: {key_info}')
    if all(k in key_info for k in("path", "passphrase", "expire")):
        await activate_key(key_info['type'], key_info)
        return web.HTTPAccepted()
    else:
        return web.HTTPBadRequest()

@routes.get('/health')
async def healthcheck(request):
    """A health endpoint for service discovery.
    It will always return ok.
    """
    LOG.debug('Healthcheck called')
    return web.HTTPOk()


@routes.get('/admin/ttl')
async def check_ttl(request):
    """Evict from the cache if TTL expired
       and return the keys that survived""" # ehh...why? /Fred
    LOG.debug('Admin TTL')
    pgp_expire = _pgp_cache.check_ttl()
    rsa_expire = _rsa_cache.check_ttl()
    if pgp_expire or rsa_expire:
        return web.json_response(pgp_expire + rsa_expire)
    else:
        return web.HTTPBadRequest()

async def load_keys_conf(store):
    """Parse and load keys configuration."""
    # Cache the active key names
    for name, value in store.defaults().items():
        if name == 'active':
            _active = value
    # Load all the keys in the store
    for section in store.sections():
        await activate_key(section, dict(store.items(section)))

alive = True  # used to set if the keyserer is alive in the shutdown

async def renew_lease(eureka, interval):
    '''Renew eureka lease at specific interval.'''
    while alive:
        await asyncio.sleep(interval)
        await eureka.renew()
        LOG.info('Keyserver Eureka lease renewed.')

async def init(app):
    '''Initialization running before the loop.run_forever'''
    app['db'] = await db.create_pool(loop=app.loop)
    LOG.info('DB Connection pool created')
    app['renew_eureka'] = app.loop.create_task(renew_lease(app['eureka'], app['interval']))
    # Note: will exit on failure
    await load_keys_conf(app['store'])
    await app['eureka'].register()
    LOG.info('Keyserver registered with Eureka.')

async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')
    global alive
    app['db'].close()
    await app['db'].wait_closed()
    await app['eureka'].deregister()
    alive = False

async def cleanup(app):
    '''Function run after a KeyboardInterrupt. Right after, the loop is closed'''
    LOG.info('Cancelling all pending tasks')
    # THIS SPAWNS an error see https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web_runner.py#L178
    # for more details how the cleanup happens.
    # for task in asyncio.Task.all_tasks():
    #     task.cancel()

def main(args=None):
    """Where the magic happens."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)

    host = CONF.get('keyserver', 'host') # fallbacks are in defaults.ini
    port = CONF.getint('keyserver', 'port')
    keyserver_health = CONF.get('keyserver', 'health_endpoint')
    keyserver_status = CONF.get('keyserver', 'status_endpoint')

    eureka_endpoint = CONF.get('eureka', 'endpoint')

    # ssl_certfile = Path(CONF.get('keyserver', 'ssl_certfile')).expanduser()
    # ssl_keyfile = Path(CONF.get('keyserver', 'ssl_keyfile')).expanduser()
    # LOG.debug(f'Certfile: {ssl_certfile}')
    # LOG.debug(f'Keyfile: {ssl_keyfile}')

    # sslcontext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # sslcontext.check_hostname = False
    # sslcontext.load_cert_chain(ssl_certfile, ssl_keyfile)

    sslcontext = None # Turning off SSL for the moment

    loop = asyncio.get_event_loop()

    keyserver = web.Application(loop=loop)
    keyserver.router.add_routes(routes)

    # Adding the keystore to the server
    keyserver['store'] = KeysConfiguration(args)
    keyserver['interval'] = CONF.getint('eureka', 'interval')
    keyserver['eureka'] = EurekaClient("keyserver", port=port, ip_addr=host,
                                       eureka_url=eureka_endpoint, hostname=host,
                                       health_check_url=f'http://{host}:{port}{keyserver_health}',
                                       status_check_url=f'http://{host}:{port}{keyserver_status}',
                                       loop=loop)

    # Registering some initialization and cleanup routines
    LOG.info('Setting up callbacks')
    keyserver.on_startup.append(init)
    keyserver.on_shutdown.append(shutdown)
    keyserver.on_cleanup.append(cleanup)

    LOG.info(f"Start keyserver on {host}:{port}")
    web.run_app(keyserver, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
