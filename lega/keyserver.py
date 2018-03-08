#!/usr/bin/env python3

'''\
Keyserver
---------

The Keyserver provides a REST endpoint for retrieving PGP and Re-encryption keys.
Active keys endpoint:

* ``/active/pgp`` - GET request for the active PGP key
* ``/active/rsa`` - GET request for the active RSA key for re-encryption
* ``/active/pgp/private`` - GET request for the private part of the active PGP key
* ``/active/pgp/public`` - GET request for the public part of the active PGP key

Retrieve keys endpoint:

* ``/retrieve/pgp/\{key_id\}`` - GET request for the active PGP key with a known keyID of fingerprint
* ``/retrieve/rsa/\{key_id\}`` - GET request for the active RSA key for re-encryption with a known keyID
* ``/retrieve/pgp/\{key_id\}/private`` - GET request for the private part of the active PGP key with a known keyID of fingerprint
* ``/retrieve/pgp/\{key_id\}/public`` - GET request for the public part of the active PGP key with a known keyID of fingerprint

Admin endpoint:

* ``/admin/unlock`` - POST request to unlock a key with a known path
* ``/admin/ttl`` - GET request to check when keys will expire

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

from .openpgp.utils import unarmor
from .openpgp.packet import iter_packets
from .conf import CONF, KeysConfiguration
from .utils import get_file_content
# from .openpgp.generate import generate_pgp_key

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


class PGPPrivateKey:
    """The Private PGP key loading."""

    def __init__(self, secret_path, passphrase):
        """Intialise PrivateKey."""
        self.secret_path = secret_path
        assert( isinstance(passphrase,str) )
        self.passphrase = passphrase.encode()
        self.key_id = None
        self.fingerprint = None

    def load_key(self):
        """Load key and return tuple for reconstruction."""
        _public_key_material = None
        _private_key_material = None
        with open(self.secret_path, 'rb') as infile:
            for packet in iter_packets(unarmor(infile)):
                LOG.info(str(packet))
                if packet.tag == 5:
                    _public_key_material, _private_key_material = packet.unlock(self.passphrase)
                    _public_length = struct.pack('>I', len(_public_key_material))
                    _private_length = struct.pack('>I', len(_private_key_material))
                    self.key_id = packet.key_id
                else:
                    packet.skip()

        return (self.key_id.upper(), (_public_length, _public_key_material, _private_length, _private_key_material))


class ReEncryptionKey:
    """ReEncryption currently done with a RSA key."""

    def __init__(self, key_id, secret_path, passphrase=''):
        """Intialise PrivateKey."""
        self.secret_path = secret_path
        self.key_id = key_id
        assert( isinstance(passphrase,str) )
        self.passphrase = passphrase.encode()

    def load_key(self):
        """Load key and return tuple for reconstruction."""
        data = get_file_content(self.secret_path)
        # unlock it with the passphrase
        # TODO
        return (self.key_id, data)


async def activate_key(key_name, data):
    """(Re)Activate a key."""
    LOG.debug(f'(Re)Activating a {key_name}')
    if key_name.startswith("pgp"):
        obj_key = PGPPrivateKey(data.get('private'), data.get('passphrase'))
        _cache = _pgp_cache
    elif key_name.startswith("rsa"):
        obj_key = ReEncryptionKey(key_name, data.get('private'), passphrase='')
        _cache = _rsa_cache
    else:
        LOG.error(f"Unrecognised key type: {key_name}")
        return

    key_id, value = obj_key.load_key()
    LOG.debug(f'Caching key: {key_id} | {key_name} in the {_cache} cache')
    if key_name == _pgp_cache.get("active_pgp_key"):
        _cache.set("active_pgp_key", key_id)
    _cache.set(key_id, value, ttl=data.get('expire', None))


# Retrieve the active keys #

@routes.get('/active/pgp')
async def active_pgp_key(request):
    """Retrieve tuple to reconstruced active unlocked key.

    In case the output is not JSON, we use the following encoding:
    First, 4 bytes for the length of the public part, followed by the public part.
    Then, 4 bytes for the length of the private part, followed by the private part.
    """
    key_id = _pgp_cache.get("active_pgp_key")
    request_type = request.content_type
    LOG.debug(f'Requested active PGP key | {request_type}')
    value = _pgp_cache.get(key_id)
    if value:
        if request_type == 'application/json':
            return web.json_response({'public': value[1].hex(), 'private': value[3].hex()})
        response_body = b''.join(value)
        if request_type == 'text/hex':
            return web.Response(body=response_body.hex(), content_type='text/hex')
        else:
            return web.Response(body=response_body, content_type='application/octed-stream')
    else:
        LOG.warn(f"Active key not found.")
        return web.HTTPNotFound()


@routes.get('/active/pgp/private')
async def active_pgp_key_private(request):
    """Retrieve private part to reconstruced unlocked active key."""
    key_id = _pgp_cache.get("active_pgp_key")
    LOG.debug(f'Requested active PGP (private) key.')
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(body=value[3].hex())
    else:
        LOG.warn(f"Requested active PGP key not found.")
        return web.HTTPNotFound()


@routes.get('/active/pgp/public')
async def active_pgp_key_public(request):
    """Retrieve public to reconstruced unlocked active key."""
    key_id = _pgp_cache.get("active_pgp_key")
    LOG.debug(f'Requested active PGP (public) key.')
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(body=value[1].hex())
    else:
        LOG.warn(f"Requested PGP key not found.")
        return web.HTTPNotFound()


@routes.get('/active/rsa')
async def retrieve_active_rsa(request):
    """Retrieve RSA reencryption key."""
    key_id = _rsa_cache.get("active_rsa_key")
    LOG.debug(f'Requested active RSA key')
    value = _rsa_cache.get(key_id)
    if value:
        return web.json_response({ 'id': key_id,
                                   'public': value.hex()})
    else:
        LOG.warn(f"Requested ReEncryption Key not found.")
        return web.HTTPNotFound()


# Just want to get a key by its key_id PGP or RSA

@routes.get('/retrieve/pgp/{requested_id}')
async def retrieve_pgp_key(request):
    """Retrieve tuple to reconstruced unlocked key.

    In case the output is not JSON, we use the following encoding:
    First, 4 bytes for the length of the public part, followed by the public part.
    Then, 4 bytes for the length of the private part, followed by the private part.
    """
    requested_id = request.match_info['requested_id']
    request_type = request.content_type
    LOG.debug(f'Requested PGP key with ID {requested_id} | {request_type}')
    key_id = requested_id[-16:].upper()
    value = _pgp_cache.get(key_id)
    if value:
        if request_type == 'application/json':
            return web.json_response({'public': value[1].hex(), 'private': value[3].hex()})
        response_body = b''.join(value)
        if request_type == 'text/hex':
            return web.Response(body=response_body.hex(), content_type='text/hex')
        else:
            return web.Response(body=response_body, content_type='application/octed-stream')
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/pgp/{requested_id}/private')
async def retrieve_pgp_key_private(request):
    """Retrieve private part to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    LOG.debug(f'Requested PGP (private) key with ID {requested_id}')
    key_id = requested_id[-16:].upper()
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(body=value[3].hex())
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/pgp/{requested_id}/public')
async def retrieve_pgp_key_public(request):
    """Retrieve public to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    LOG.debug(f'Requested PGP (public) key with ID {requested_id}')
    key_id = requested_id[-16:].upper()
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(body=value[1].hex())
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/rsa/{requested_id}')
async def retrieve_reencryt_key(request):
    """Retrieve RSA reencryption key."""
    requested_id = request.match_info['requested_id']
    LOG.debug(f'Requested RSA key with ID {requested_id}')
    value = _rsa_cache.get(requested_id)
    if value:
        return web.json_response({ 'id': requested_id,
                                   'public': value.hex()})
    else:
        LOG.warn(f"Requested ReEncryption Key not found.")
        return web.HTTPNotFound()


@routes.post('/admin/unlock')
async def unlock_key(request):
    """Unlock a key via a POST request.
    POST request takes the form:
    \{"type": "pgp", "private": "path/to/file.sec", "passphrase": "pass", "expire": "30/MAR/18 08:00:00"\}
    """
    key_info = await request.json()
    LOG.debug(f'Admin unlocking: {key_info}')
    if all(k in key_info for k in("private", "passphrase", "expire")):
        await activate_key(key_info['type'], key_info)
        return web.HTTPAccepted()
    else:
        return web.HTTPBadRequest()


# @routes.post('generate/pgp')
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


@routes.get('/admin/ttl')
async def check_ttl(request):
    """Evict from the cache if TTL expired
       and return the keys that survived""" # ehh...why? /Fred
    LOG.debug(f'Admin TTL')
    pgp_expire = _pgp_cache.check_ttl()
    rsa_expire = _rsa_cache.check_ttl()
    if pgp_expire or rsa_expire:
        return web.json_response(pgp_expire + rsa_expire)
    else:
        return web.HTTPBadRequest()


async def load_keys_conf(KEYS):
    """Parse and load keys configuration."""
    # Cache the active key names
    for name, value in KEYS.defaults().items():
        if name == 'pgp':
            _pgp_cache.set('active_pgp_key', value)
        if name == 'rsa':
            _rsa_cache.set('active_rsa_key', value)
    # Load all the keys in the store
    for section in KEYS.sections():
        await activate_key(section, dict(KEYS.items(section)))


def main(args=None):
    """Where the magic happens."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)
    KEYS = KeysConfiguration(args)

    host = CONF.get('keyserver', 'host') # fallbacks are in defaults.ini
    port = CONF.getint('keyserver', 'port')

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

    loop.run_until_complete(load_keys_conf(KEYS))

    LOG.info(f"Start keyserver on {host}:{port}")
    web.run_app(keyserver, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
