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
        if not ttl:
            ttl = self._ttl
        else:
            ttl = self._parse_date_time(ttl)
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
        self.passphrase = passphrase.encode()
        self.key_id = None
        self.fingerprint = None

    def load_key(self):
        """Load key and return tuble for reconstruction."""
        _public_key_material = None
        _private_key_material = None
        with open(self.secret_path, 'rb') as infile:
            for packet in iter_packets(unarmor(infile)):
                LOG.info(str(packet))
                if packet.tag == 5:
                    _public_key_material, _private_key_material = packet.unlock(self.passphrase)
                    _public_lenght = struct.pack('>I', len(_public_key_material))
                    _private_lenght = struct.pack('>I', len(_private_key_material))
                    self.key_id = packet.key_id
                else:
                    packet.skip()

        return (self.key_id, (_public_lenght + _public_key_material, _private_lenght+_private_key_material))


class ReEncryptionKey:
    """ReEncryption currently done with a RSA key."""

    def __init__(self, secret_path):
        """Intialise PrivateKey."""
        self.secret_path = secret_path

    def load_key(self):
        """Load key and return tuble for reconstruction."""
        with open(self.secret_path, 'rb') as infile:
            data = infile.read()
            return data.decode()


# For now, one must know the path of the Key to re(activate) it
async def activate_key(key_info):
    """(Re)Activate a key."""
    if key_info["type"] == "pgp":
        obj_key = PGPPrivateKey(key_info['path'], key_info['passphrase'])
        key_id, value = obj_key.load_key()
        _pgp_cache.set(key_id, value, ttl=key_info['ttl'])
    elif key_info["type"] == "rsa":
        obj_key = ReEncryptionKey(key_info['path'])
        value = obj_key.load_key()
        _rsa_cache.set("rsa", value)
    else:
        LOG.error(f"Unrecognised key type.")


@routes.get('/retrieve/pgp/{requested_id}')
async def retrieve_pgp_key(request):
    """Retrieve tuple to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    request_type = request.content_type
    key_id = requested_id[-16:]
    value = _pgp_cache.get(key_id)
    if value:
        response_body = value[0]+value[1]
        if request_type == 'application/json':
            return web.json_response({'public': value[0].hex(), 'private': value[1].hex()})
        if request_type == 'text/hexa':
            return web.Response(body=response_body.hex(), content_type='text/hexa')
        else:
            return web.Response(body=response_body, content_type='application/octed-stream')
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/pgp/private/{requested_id}')
async def retrieve_pgp_key_private(request):
    """Retrieve private part to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    print(request.content_type)
    key_id = requested_id[-16:]
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(content=value[1].hex())
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/pgp/public/{requested_id}')
async def retrieve_pgp_key_public(request):
    """Retrieve public to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    print(request.content_type)
    key_id = requested_id[-16:]
    value = _pgp_cache.get(key_id)
    if value:
        return web.Response(content=value[0].hex())
    else:
        LOG.warn(f"Requested PGP key {requested_id} not found.")
        return web.HTTPNotFound()


@routes.get('/retrieve/rsa')
async def retrieve_reencryt_key(request):
    """Retrieve RSA reencryption key."""
    value = _rsa_cache.get("rsa")
    if value:
        return web.Response(text=value)
    else:
        LOG.warn(f"Requested ReEncryption Key not found.")
        return web.HTTPNotFound()


@routes.post('/admin/unlock')
async def unlock_key(request):
    """Unlock a key via request."""
    key_info = await request.json()
    if all(k in key_info for k in("path", "passphrase", "ttl")):
        key_info["type"] = "pgp"
        await activate_key(key_info)
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
    pgp_key = {"type": "pgp",
               "path": KEYS.get(active_pgp_key, 'private'),
               "passphrase": KEYS.get(active_pgp_key, 'passphrase'),
               "ttl": KEYS.get('PGP', 'EXPIRE', fallback=None)}

    rsa_key = {"type": "rsa",
               "path": KEYS.get(active_rsa_key, 'PATH'),
               "ttl": KEYS.get('REENCRYPTION_KEYS', 'EXPIRE', fallback=None)}

    await activate_key(pgp_key)
    await activate_key(rsa_key)


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
