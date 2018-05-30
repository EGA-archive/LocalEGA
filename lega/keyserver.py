#!/usr/bin/env python3

'''\
Keyserver
---------

The Keyserver provides a REST endpoint for retrieving PGP and Re-encryption keys.
Active keys endpoint (current key types supported are PGP and RSA):

* ``/active/\{key_type\}`` - GET request for the active key
* ``/active/\{key_type\}/private`` - GET request for the private part of the active key
* ``/active/\{key_type\}/public`` - GET request for the public part of the active key

Retrieve keys endpoint:

* ``/retrieve/\{key_type\}/\{key_id\}`` - GET request for the active PGP key with a known keyID of fingerprint
* ``/retrieve/\{key_type\}/\{key_id\}/private`` - GET request for the private part of the active PGP key with a known keyID of fingerprint
* ``/retrieve/\{key_type\}/\{key_id\}/public`` - GET request for the public part of the active PGP key with a known keyID of fingerprint

Admin endpoint:

* ``/admin/unlock`` - POST request to unlock a key with a known path
* ``/admin/ttl`` - GET request to check when keys will expire

'''
# Generate endpoint:
#
# * ``/generate/pgp`` - POST request to generate a PGP key pair

import sys
import asyncio
from aiohttp import web
import logging
import time
import datetime
from pathlib import Path
import ssl
import struct

from .openpgp.utils import unarmor
from .openpgp.packet import iter_packets
from .conf import CONF, KeysConfiguration
from .utils import get_file_content, db
from .utils.crypto import get_rsa_private_key_material, serialize_rsa_private_key
# from .openpgp.generate import generate_pgp_key
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
        """Assign in the store to the the key the value, its ttl, and if it is active."""
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
            if expire is None and key not in ('active_pgp_key', 'active_rsa_key'):
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


# All the cache goes here
_pgp_cache = Cache() # keys are uppercase
_rsa_cache = Cache()
_tmp_cache = Cache()


class PGPPrivateKey:
    """The Private PGP key loading."""

    def __init__(self, path, passphrase):
        """Intialise PrivateKey."""
        self.path = path
        assert( isinstance(passphrase,str) )
        self.passphrase = passphrase.encode()
        self.key_id = None
        self.fingerprint = None

    def load_key(self):
        """Load key and return tuple for reconstruction."""
        data = None
        with open(self.path, 'rb') as infile:
            for packet in iter_packets(unarmor(infile)):
                LOG.info(str(packet))
                if packet.tag == 5:
                    data = packet.unlock(self.passphrase)
                    self.key_id = packet.key_id
                else:
                    packet.skip()

        return (self.key_id.upper(), data)


class ReEncryptionKey:
    """ReEncryption currently done with a RSA key."""

    def __init__(self, key_id, path, passphrase):
        """Intialise PrivateKey."""
        self.path = path
        self.key_id = key_id
        self.passphrase = passphrase

    def load_key(self):
        """Load key and unlocks it."""
        with open(self.path, 'rb') as infile:
            data = get_rsa_private_key_material(infile.read(), password=self.passphrase)
            data['id'] = self.key_id
            return (self.key_id, data)


###############################
## Temp endpoint
###############################
@routes.get('/temp/rsa/{requested_id}')
async def temp_key(request):
    """Returns the unprotected file content"""
    requested_id = request.match_info['requested_id']
    LOG.debug(f'Requested raw rsa keyfile with ID {requested_id}')
    value = _tmp_cache.get(requested_id)
    if value:
        return web.Response(text=value.hex())
    else:
        LOG.warn(f"Requested raw keyfile for {requested_id} not found.")
        return web.HTTPNotFound()

####################################
# Caching the keys
####################################

async def activate_key(key_name, data):
    """(Re)Activate a key."""
    LOG.debug(f'(Re)Activating a {key_name}')
    if key_name.startswith("pgp"):
        obj_key = PGPPrivateKey(data.get('path'), data.get('passphrase'))
        _cache = _pgp_cache
    elif key_name.startswith("rsa"):
        obj_key = ReEncryptionKey(key_name, data.get('path'), data.get('passphrase',None))
        _cache = _rsa_cache
        
        ### Temporary
        with open(data.get('path'), 'rb') as infile:
            _tmp_cache.set(key_name,
                           serialize_rsa_private_key(infile.read(), password=data.get('passphrase',None))
            )

    else:
        LOG.error(f"Unrecognised key type: {key_name}")
        return

    key_id, value = obj_key.load_key()
    LOG.debug(f'Caching key: {key_id} | {key_name} in the {_cache} cache')
    if key_name == _pgp_cache.get("active_pgp_key"):
        _cache.set("active_pgp_key", key_id)
    _cache.set(key_id, value, ttl=data.get('expire', None))

####################################
# Retrieve the active keys
####################################

@routes.get('/active/{key_type}')
async def active_key(request):
    """Returns a JSON-formated list of numbers to reconstruct the active key, unlocked.

    For PGP key types:

        * The JOSN response contains a "type" attribute to specify which key it is.
        * If type is "rsa", the public and private attributes contain ('n','e') and ('d','p','q','u') respectively.
        * If type is "dsa", the public and private attributes contain ('p','q','g','y') and ('x') respectively.
        * If type is "elg", the public and private attributes contain ('p','g','y') and ('x') respectively.

    For RSA the public and private parts are retrieved in hex format.

    Other key types are not supported.
    """
    key_type = request.match_info['key_type'].lower()
    if key_type == 'pgp':
        active_key = "active_pgp_key"
        _cache = _pgp_cache
    elif key_type == 'rsa':
        active_key = "active_rsa_key"
        _cache = _rsa_cache
    else:
        return web.HTTPBadRequest()
    key_id = _cache.get(active_key)
    LOG.debug(f'Requesting active %s key', key_type.upper())
    value = _cache.get(key_id)
    if value:
        return web.json_response(value)
    else:
        LOG.warn(f"Active key not found.")
        return web.HTTPNotFound()


@routes.get('/active/{key_type}/private')
async def active_key_private(request):
    """Retrieve private part to reconstruced unlocked active key.

    For PGP key types:

        * The JOSN response contains a "type" attribute to specify which key it is.
        * If type is "rsa", the private attribute contains ('d','p','q','u').
        * If type is "dsa", the private attribute contains ('x').
        * If type is "elg", the private attribute contains ('x').

    For RSA the public and private parts are retrieved in hex format.

    Other key types are not supported.
    """
    key_type = request.match_info['key_type'].lower()
    if key_type == 'pgp':
        active_key = "active_pgp_key"
        _cache = _pgp_cache
    elif key_type == 'rsa':
        active_key = "active_rsa_key"
        _cache = _rsa_cache
    else:
        return web.HTTPBadRequest()
    key_id = _cache.get(active_key)
    LOG.debug(f'Requesting active %s (private) key', key_type.upper())
    value = dict(_cache.get(key_id))
    if value:
        del value['public']
        return web.json_response(value)
    else:
        LOG.warn(f"Requested active %s (private) key not found.", key_type.upper())
        return web.HTTPNotFound()


@routes.get('/active/{key_type}/public')
async def active_key_public(request):
    """Retrieve public to reconstruced unlocked active key.

    For PGP key types:

        * The JOSN response contains a "type" attribute to specify which key it is.
        * If type is "rsa", the public attribute contains ('n','e').
        * If type is "dsa", the public attribute contains ('p','q','g','y').
        * If type is "elg", the public attribute contains ('p','g','y').

    For RSA the public part is retrieved in hex format.

    Other key types are not supported.
    """
    key_type = request.match_info['key_type'].lower()
    if key_type == 'pgp':
        active_key = "active_pgp_key"
        _cache = _pgp_cache
    elif key_type == 'rsa':
        active_key = "active_rsa_key"
        _cache = _rsa_cache
    else:
        return web.HTTPBadRequest()
    key_id = _cache.get(active_key)
    LOG.debug(f'Requesting active %s (public) key', key_type.upper())
    value = dict(_cache.get(key_id))
    if value:
        del value['private']
        return web.json_response(value)
    else:
        LOG.warn(f"Requested %s key (public) not found.", key_type.upper())
        return web.HTTPNotFound()


# Just want to get a key by its key_id PGP or RSA

@routes.get('/retrieve/{key_type}/{requested_id}')
async def retrieve_key(request):
    """Returns a JSON-formated list of numbers to reconstruct an unlocked key.

    For PGP key types:

        * The JOSN response contains a "type" attribute to specify which key it is.
        * If type is "rsa", the public and private attributes contain ('n','e') and ('d','p','q','u') respectively.
        * If type is "dsa", the public and private attributes contain ('p','q','g','y') and ('x') respectively.
        * If type is "elg", the public and private attributes contain ('p','g','y') and ('x') respectively.

    For RSA the public and private parts are retrieved in hex format.

    Other key types are not supported.
    """
    requested_id = request.match_info['requested_id']
    key_type = request.match_info['key_type'].lower()
    if key_type == 'pgp':
        _cache = _pgp_cache
        key_id = requested_id[-16:].upper()
    elif key_type == 'rsa':
        _cache = _rsa_cache
        key_id = requested_id
    else:
        return web.HTTPBadRequest()
    LOG.debug(f'Requested {key_type.upper()} key with ID {requested_id}')
    value = _cache.get(key_id)
    if value:
        return web.json_response(value)
    else:
        LOG.warn(f"Requested {key_type.upper()} key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/{key_type}/{requested_id}/private')
async def retrieve_key_private(request):
    """Retrieve private part to reconstruct unlocked key.

    :py:func:`lega.keyserver.active_key_private`
    """
    requested_id = request.match_info['requested_id']
    key_type = request.match_info['key_type'].lower()
    if key_type == 'pgp':
        _cache = _pgp_cache
        key_id = requested_id[-16:].upper()
    elif key_type == 'rsa':
        _cache = _rsa_cache
        key_id = requested_id
    else:
        return web.HTTPBadRequest()
    LOG.debug(f'Requested {key_type.upper()} (private) key with ID {requested_id}')
    value = dict(_cache.get(key_id))
    if value:
        del value['public']
        return web.json_response(value)
    else:
        LOG.warn(f"Requested {key_type.upper()} (private) key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/{key_type}/{requested_id}/public')
async def retrieve_key_public(request):
    """Retrieve public part to reconstruct unlocked key.

    :py:func:`lega.keyserver.active_key_private`
    """
    requested_id = request.match_info['requested_id']
    key_type = request.match_info['key_type'].lower()
    if key_type == 'pgp':
        _cache = _pgp_cache
        key_id = requested_id[-16:].upper()
    elif key_type == 'rsa':
        _cache = _rsa_cache
        key_id = requested_id
    else:
        return web.HTTPBadRequest()
    LOG.debug(f'Requested {key_type.upper()} (public) key with ID {requested_id}')
    value = dict(_cache.get(key_id))
    if value:
        del value['private']
        return web.json_response(value)
    else:
        LOG.warn(f"Requested {key_type.upper()} (public) key {requested_id} not found.")
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


# @routes.post('/generate/pgp')
# async def generate_pgp_key_pair(request):
#     """Generate PGP key pair"""
#     key_options = await request.json()
#     LOG.debug(f'Admin generate PGP key pair: {key_options}')
#     if all(k in key_options for k in("name", "comment", "email")):
#         # By default we can return armored
#         pub_data, sec_data = generate_pgp_key(key_options['name'],
#                                               key_options['email'],
#                                               key_options['comment'],
#                                               key_options.get('passphrase', None))
#         # TO DO return the key pair or the path where it is stored.
#         return web.HTTPAccepted()
#     else:
#         return web.HTTPBadRequest()


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

@routes.get('/temp/file/{file_id}')
async def id2info(request):
    """Translate a file_id to a file info"""
    file_id = request.match_info['file_id']
    LOG.debug(f'Translation {file_id} to fileinfo')
    fileinfo = await db.get_fileinfo(request.app['db'], file_id)
    if fileinfo:
        filepath, filesize, checksum, algo = fileinfo # unpack
        return web.json_response({
            'filepath': filepath,
            'filesize': filesize,
            'checksum': checksum,
            'algo': algo,
        })
    raise web.HTTPNotFound(text=f'Dunno anything about a file with id "{file_id}"\n')

async def load_keys_conf(store):
    """Parse and load keys configuration."""
    # Cache the active key names
    for name, value in store.defaults().items():
        if name == 'pgp':
            _pgp_cache.set('active_pgp_key', value)
        if name == 'rsa':
            _rsa_cache.set('active_rsa_key', value)
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
