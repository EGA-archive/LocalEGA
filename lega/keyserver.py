#!/usr/bin/env python3

import sys
import asyncio
from aiohttp import web
import logging
import time
import datetime
from pathlib import Path
from collections import OrderedDict
import ssl

from .openpgp.utils import unarmor
from .openpgp.packet import iter_packets
from .conf import CONF, KeysConfiguration

LOG = logging.getLogger('keyserver')
routes = web.RouteTableDef()

ACTIVE_KEYS = {}
# For the match, we turn that off
ssl.match_hostname = lambda cert, hostname: True


class Cache:
    """In memory cache."""

    def __init__(self, max_size=10, timeout=None):
        """Initialise cache."""
        self._store = OrderedDict()
        self._max_size = max_size
        self._timeout = timeout

    def set(self, key, value, timeout=None):
        """Assign in the store to the the key the value and timeout."""
        self._check_limit()
        if not timeout:
            timeout = self._timeout
        else:
            timeout = self._parse_date_time(timeout)
        self._store[key] = (value, timeout)

    def get(self, key):
        """Retrieve value based on key."""
        data = self._store.get(key)
        if not data:
            return None
        value, expire = data
        if expire and time.time() > expire:
            del self._store[key]
            return None
        return value

    def _parse_date_time(self, date_time):
        """We allow timeout to be specified by date and time.

        Example of set time and date 30/MAR/18 08:00:00 .
        """
        return time.mktime(datetime.datetime.strptime(date_time, "%d/%b/%y %H:%M:%S").timetuple())

    def _check_limit(self):
        """Check if current cache size exceeds maximum cache size and pop the oldest item in this case."""
        if len(self._store) >= self._max_size:
            self._store.popitem(last=False)

    def clear(self):
        """Clear all cache."""
        self._store = OrderedDict()


# All the cache goes here
cache = Cache()


class PrivateKey:
    """The Private Key loading and retrieving parts."""

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
                    self.key_id = packet.key_id
                else:
                    packet.skip()

        # TO DO return a _tuple, fingerprint
        return (self.key_id, (_public_key_material, _private_key_material))


async def keystore(key_list):
    """Start a cache "keystore" with default active keys."""
    start_time = time.time()
    objects = [(PrivateKey(key_list[i][0], key_list[i][1]), key_list[i][3]) for i in key_list]
    for obj in objects:
        key_id, values = obj[0].load_key()
        cache.set(key_id, values, timeout=obj[1])

    LOG.info(f"Keystore loaded keys in: {(time.time() - start_time)} seconds ---")


@routes.get('/retrieve/{requested_id}')
async def retrieve_key(request):
    """Retrieve tuple to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    start_time = time.time()
    key_id = requested_id[-16:]
    value = cache.get(key_id)
    if value:
        LOG.info(f"Retrived private key with id {key_id} in: {(time.time() - start_time)} seconds ---")
        return web.json_response(value)
    else:
        LOG.warn("Requested key {requested_id} not found.")
        return web.HTTPNotFound()


# @routes.get('/admin/unlock/{key_id}')
# async def unlock_key(request):


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

    sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS)
    sslcontext.load_cert_chain(ssl_certfile, ssl_keyfile)

    if not sslcontext:
        LOG.error('No SSL encryption. Exiting...')
    else:
        sslcontext = None
        LOG.info('With SSL encryption')

    for i, key in enumerate(KEYS.get('KEYS', 'active').split(",")):
        ls = [KEYS.get(key, 'PATH'), KEYS.get(key, 'PASSPHRASE'), KEYS.get(key, 'EXPIRE')]
        ACTIVE_KEYS[i] = tuple(ls)

    host = CONF.get('keyserver', 'host')
    port = CONF.getint('keyserver', 'port')
    loop = asyncio.get_event_loop()

    loop.run_until_complete(keystore(ACTIVE_KEYS))

    keyserver = web.Application(loop=loop)
    keyserver.router.add_routes(routes)

    LOG.info("Start keyserver")
    web.run_app(keyserver, host=host, port=port, shutdown_timeout=0, loop=loop, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
