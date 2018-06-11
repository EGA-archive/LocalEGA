#!/usr/bin/env python3

'''\
The Keyserver provides a REST endpoint for retrieving PGP and Re-encryption keys.
The keyserver also registers with Eureka service discovery.
'''


import sys
import os
import logging
import time
import datetime
import asyncio
from pathlib import Path
import ssl
import secrets
import string

from aiohttp import web
import pgpy

from .conf import CONF, KeysConfiguration
from .utils.eureka import EurekaClient

LOG = logging.getLogger(__name__)
routes = web.RouteTableDef()

class Cache:
    """In memory cache."""

    def __init__(self, max_size=10, ttl=None):
        """Initialise cache."""
        self.store = dict()
        self.max_size = max_size
        self.ttl = ttl
        self.FMT = '%d/%b/%y %H:%M:%S'
        self.key = os.environ.get('LEGA_PASSWORD', None)  # must exist
        assert self.key, "The key needs a password."

    def set(self, keyid, key, ttl=None):
        """Assign in the store to the the key the value, its ttl."""
        self._check_limit()
        ttl = self.ttl if not ttl else self._parse_date_time(ttl)
        assert key.is_protected and key.is_unlocked, "The PGPKey must be protected and unlocked"
        key.protect(self.key, pgpy.constants.SymmetricKeyAlgorithm.AES256, pgpy.constants.HashAlgorithm.SHA256)  # re-protect
        self.store[keyid] = (bytes(key.pubkey), bytes(key), ttl)

    def get(self, keyid, key_type):
        """Retrieve value based on key."""
        data = self.store.get(keyid)
        if not data:
            return None
        pubkey, privkey, expire = data
        if expire and time.time() > expire:
            del self.store[keyid]
            return None
        if key_type == 'public':
            return pubkey
        if key_type == 'private':
            return privkey
        return None

    def check_ttl(self):
        """Check ttl for all keys."""
        keys = []
        for key, (_, _, expire) in self.store.items():
            if expire and time.time() < expire:
                keys.append({"keyID": key, "ttl": self._time_delta(expire)})
            if expire is None:
                keys.append({"keyID": key, "ttl": "Expiration not set."})
        return keys

    def _time_delta(self, expire):
        """"Convert time left in human readable format."""
        # A lot of back and forth transformation
        end_time = datetime.datetime.fromtimestamp(expire).strftime(self.FMT)
        today = datetime.datetime.today().strftime(self.FMT)
        tdelta = datetime.datetime.strptime(end_time, self.FMT) - datetime.datetime.strptime(today, self.FMT)

        if tdelta.days > 0:
            tdelta = datetime.timedelta(days=tdelta.days, seconds=tdelta.seconds)
            return f"{tdelta.days} days {tdelta.days * 24 + tdelta.seconds // 3600} hours {(tdelta.seconds % 3600) // 60} minutes {tdelta.seconds} seconds"

    def _parse_date_time(self, date_time):
        """We allow ttl to be specified by date and time.

        Example of set time and date 30/MAR/18 08:00:00 .
        """
        return time.mktime(datetime.datetime.strptime(date_time, self.FMT).timetuple())

    def _check_limit(self):
        """Check if current cache size exceeds maximum cache size and pop the oldest item in this case."""
        if len(self.store) >= self.max_size:
            self.store.popitem(last=False)

    def clear(self):
        """Clear all cache."""
        #self.store = dict()
        self.store.clear()


_cache = None  # key IDs are uppercase
_active = None # will be a KeyID (not a key name)

####################################
# Caching the keys
####################################

def _unlock_key(name, active=None, path=None, expire=None, passphrase=None, **kwargs):
    """Unlocking a key and loading it in the cache."""
    key, _ = pgpy.PGPKey.from_file(path)
    assert not key.is_public, f"The key {name} should be private"
    with key.unlock(passphrase) as k:
        key_id = k.fingerprint.keyid.upper()
        LOG.debug(f'Activating key: {key_id} ({name})')
        _cache.set(key_id, k, ttl=expire)
        if active and name == active:
            global _active
            _active = key_id


####################################
# Retrieve the active keys
####################################

@routes.get('/active/{key_type}')
async def retrieve_active_key(request):
    key_type = request.match_info['key_type'].lower()
    LOG.debug(f'Requesting active ({key_type}) key')
    if key_type not in ('public', 'private'):
        return web.HTTPForbidden() # web.HTTPBadRequest()
    if _active is None:
        return web.HTTPNotFound()
    k = _cache.get(_active, key_type)
    if k:
        return web.Response(body=k) # web.Response(text=k.hex())
    else:
        LOG.warn(f"Requested active ({key_type}) key not found.")
        return web.HTTPNotFound()

@routes.get('/retrieve/{requested_id}/{key_type}')
async def retrieve_key(request):
    LOG.debug('Retrieve key')
    requested_id = request.match_info['requested_id']
    key_type = request.match_info['key_type'].lower()
    if key_type not in ('public', 'private'):
        return web.HTTPForbidden() # web.HTTPBadRequest()
    key_id = requested_id[-16:].upper()
    LOG.debug(f'Requested {key_type.upper()} key with ID {requested_id}')
    k = _cache.get(key_id, key_type)
    if k:
        return web.Response(body=k) # web.Response(text=value.hex())
    else:
        LOG.warn(f"Requested key {requested_id} not found.")
        return web.HTTPNotFound()

@routes.post('/admin/unlock')
async def unlock_key(request):
    """Unlock a key via a POST request.
    POST request takes the form:
    \{"private": "path/to/file.sec", "passphrase": "pass", "expire": "30/MAR/18 08:00:00"\}
    """
    key_info = await request.json()
    LOG.debug(f'Admin unlocking: {key_info}')
    if all(k in key_info for k in("path", "passphrase", "expire")):
        _unlock_key('whichname?', **key_info)
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
    expire = _cache.check_ttl()
    if expire:
        return web.json_response(expire)
    else:
        return web.HTTPBadRequest()

def load_keys_conf(store):
    """Parse and load keys configuration."""
    # Cache the active key names
    global _cache
    _cache = Cache()
    # Load all the keys in the store
    for section in store.sections():
        _unlock_key(section, **dict(store.items(section))) # includes defaults

alive = True  # used to set if the keyserver is alive in the shutdown

async def renew_lease(eureka, interval):
    '''Renew eureka lease at specific interval.'''
    while alive:
        await asyncio.sleep(interval)
        await eureka.renew()
        LOG.info('Keyserver Eureka lease renewed.')

async def init(app):
    '''Initialization running before the loop.run_forever'''
    app['renew_eureka'] = app.loop.create_task(renew_lease(app['eureka'], app['interval']))
    # Note: will exit on failure
    load_keys_conf(app['store'])
    await app['eureka'].register()
    LOG.info('Keyserver registered with Eureka.')

async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')
    global alive
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
    health_check_url='http://{}:{}{}'.format(host, port, CONF.get('keyserver', 'health_endpoint'))
    status_check_url='http://{}:{}{}'.format(host, port, CONF.get('keyserver', 'status_endpoint'))

    eureka_endpoint = CONF.get('eureka', 'endpoint')

    ssl_certfile = Path(CONF.get('keyserver', 'ssl_certfile')).expanduser()
    ssl_keyfile = Path(CONF.get('keyserver', 'ssl_keyfile')).expanduser()
    LOG.debug(f'Certfile: {ssl_certfile}')
    LOG.debug(f'Keyfile: {ssl_keyfile}')

    sslcontext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    sslcontext.check_hostname = False
    sslcontext.load_cert_chain(ssl_certfile, ssl_keyfile)

    loop = asyncio.get_event_loop()

    keyserver = web.Application(loop=loop)
    keyserver.router.add_routes(routes)

    # Adding the keystore to the server
    keyserver['store'] = KeysConfiguration(args)
    keyserver['interval'] = CONF.getint('eureka', 'interval')
    keyserver['eureka'] = EurekaClient("keyserver", port=port, ip_addr=host,
                                       eureka_url=eureka_endpoint, hostname=host,
                                       health_check_url=health_check_url,
                                       status_check_url=status_check_url,
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
