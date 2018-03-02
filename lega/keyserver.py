#!/usr/bin/env python3

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

LOG = logging.getLogger('keyserver')
routes = web.RouteTableDef()

ACTIVE_KEYS = {}


class Cache:
    """In memory cache."""

    def __init__(self, max_size=10, ttl=None):
        """Initialise cache."""
        self._store = dict()
        self._max_size = max_size
        self._ttl = ttl
        self._FMT = '%d/%b/%y %H:%M:%S'

    def set(self, key, value, ttl=None):
        """Assign in the store to the the key the value and ttl."""
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
        """Check ttl for active keys."""
        keys = []
        for key, data in self._store.items():
            value, expire = data
            if expire and time.time() > expire:
                del self._store[key]
            if expire:
                keys.append({"keyID": key, "ttl": self._time_delta(expire)})
            return keys

    def _time_delta(self, expire):
        """"Convert time left in huma readable format."""
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
_pgp_cache = Cache()
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

        return (self.key_id, (_public_length, _public_key_material, _private_length, _private_key_material))


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


# For now, one must know the path of the Key to re(activate) it
async def activate_key(key_type, path, key_id=None, ttl=None, passphrase=None):
    """(Re)Activate a key."""
    if key_type == "pgp":
        obj_key = PGPPrivateKey(path, passphrase)
        _cache = _pgp_cache
    elif key_type == "rsa":
        assert( key_id is not None )
        obj_key = ReEncryptionKey(key_id, path, passphrase='')
        _cache = _rsa_cache
    else:
        LOG.error(f"Unrecognised key type.")

    key_id, value = obj_key.load_key()
    _cache.set(key_id, value, ttl=ttl)

@routes.get('/retrieve/pgp/{requested_id}')
async def retrieve_pgp_key(request):
    """Retrieve tuple to reconstruced unlocked key.

    In case the output is not JSON, we use the following encoding:
    First, 4 bytes for the length of the public part, followed by the public part.
    Then, 4 bytes for the length of the private part, followed by the private part."""
    requested_id = request.match_info['requested_id']
    request_type = request.content_type
    key_id = requested_id[-16:]
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


@routes.get('/retrieve/pgp/private/{requested_id}')
async def retrieve_pgp_key_private(request):
    """Retrieve private part to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    key_id = requested_id[-16:]
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(body=value[3].hex())
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/pgp/public/{requested_id}')
async def retrieve_pgp_key_public(request):
    """Retrieve public to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    key_id = requested_id[-16:]
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(body=value[1].hex())
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/reencryptionkey')
async def retrieve_reencryt_key(request):
    """Retrieve RSA reencryption key."""
    key_id = _rsa_cache.get("active_rsa_key")
    value = _rsa_cache.get(key_id)
    if value:
        return web.json_response({ 'id': key_id,
                                   'public': value.hex()})
    else:
        LOG.warn(f"Requested ReEncryption Key not found.")
        return web.HTTPNotFound()


@routes.post('/admin/unlock')
async def unlock_key(request):
    """Unlock a key via request."""
    key_info = await request.json()
    if all(k in key_info for k in("path", "passphrase", "ttl")):
        await activate_key('pgp', key_info['path'], passphrase=key_info['passphrase'], ttl=key_info['ttl'])
        return web.HTTPAccepted()
    else:
        return web.HTTPBadRequest()


@routes.get('/admin/ttl')
async def check_ttl(request):
    """Unlock a key via request."""
    pgp_expire = _pgp_cache.check_ttl()
    rsa_expire = _rsa_cache.check_ttl()
    if pgp_expire or rsa_expire:
        return web.json_response(pgp_expire + rsa_expire)
    else:
        return web.HTTPBadRequest()


async def load_keys_conf(KEYS):
    """Parse and load keys configuration."""
    active_pgp_key = KEYS.get('PGP', 'active')
    active_rsa_key = KEYS.get('REENCRYPTION_KEYS', 'active')
    await activate_key('pgp',
                       path=KEYS.get(active_pgp_key, 'private'),
                       passphrase=KEYS.get(active_pgp_key, 'passphrase'),
                       ttl=KEYS.get('PGP', 'EXPIRE', fallback=None),
                       key_id=None)
    await activate_key('rsa',
                       path=KEYS.get(active_rsa_key, 'PATH'),
                       passphrase=None,
                       ttl=KEYS.get('REENCRYPTION_KEYS', 'EXPIRE', fallback=None),
                       key_id=active_rsa_key)
    _rsa_cache.set('active_rsa_key', active_rsa_key)


def main(args=None):
    """Where the magic happens."""
    if not args:
        args = sys.argv[1:]

    CONF.setup(args)
    KEYS = KeysConfiguration(args)

    ssl_certfile = Path(CONF.get('keyserver', 'ssl_certfile')).expanduser()
    ssl_keyfile = Path(CONF.get('keyserver', 'ssl_keyfile')).expanduser()
    LOG.debug(f'Certfile: {ssl_certfile}')
    LOG.debug(f'Keyfile: {ssl_keyfile}')

    # sslcontext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    sslcontext.check_hostname = False
    sslcontext.load_cert_chain(ssl_certfile, ssl_keyfile)

    host = CONF.get('keyserver', 'host')
    port = CONF.getint('keyserver', 'port')
    loop = asyncio.get_event_loop()

    keyserver = web.Application(loop=loop)
    keyserver.router.add_routes(routes)

    loop.run_until_complete(load_keys_conf(KEYS))

    LOG.info("Start keyserver")
    web.run_app(keyserver, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
