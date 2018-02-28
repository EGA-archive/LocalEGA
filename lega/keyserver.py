#!/usr/bin/env python3

import sys
import asyncio
from aiohttp import web
import logging
import aiocache
import time
from pathlib import Path
import ssl

from .openpgp.utils import unarmor
from .openpgp.packet import iter_packets
from .utils.exceptions import PGPError
from .conf import CONF, KeysConfiguration

from aiocache.plugins import TimingPlugin
from aiocache.serializers import JsonSerializer

LOG = logging.getLogger('keyserver')
routes = web.RouteTableDef()
cache = aiocache.SimpleMemoryCache(plugins=[TimingPlugin()],
                                   serializer=JsonSerializer())

ACTIVE_KEYS = {}


class PrivateKey:
    """The Private Key loading and retrieving parts."""

    def __init__(self, secret_key, passphrase):
        """Intialise PrivateKey."""
        self.secret_key = secret_key
        self.passphrase = passphrase.encode()
        self.key_id = None
        self.fingerprint = None

    def retrieve_tuple(self, alg_type, private_nb):
        """Depending on the algorithm type return the tuple dict."""
        # This could also be a namedtuple
        tupled = set()
        if alg_type == "rsa":
            tupled = {'n': private_nb.public_numbers.n,
                      'e': private_nb.public_numbers.e,
                      'd': private_nb.d,
                      'p': private_nb.p,
                      'q': private_nb.q}
        elif alg_type == "dsa":
            tupled = {'y': private_nb.public_numbers.y,
                      'g': private_nb.public_numbers.parameter_numbers.g,
                      'p': private_nb.public_numbers.parameter_numbers.p,
                      'q': private_nb.public_numbers.parameter_numbers.q,
                      'x': private_nb.x}
        elif alg_type == "elg":
            tupled = {'p': private_nb.public_numbers.parameter_numbers.p,
                      'g': private_nb.public_numbers.parameter_numbers.g,
                      'y': private_nb.public_numbers.y,
                      'x': private_nb.x}
        else:
            raise PGPError('Unsupported asymmetric algorithm')

        return tupled

    def load_key(self):
        """Load key and return tuble for reconstruction."""
        _tupled = {}
        with open(self.secret_key, 'rb') as infile:
            for packet in iter_packets(unarmor(infile)):
                LOG.info(str(packet))
                if packet.tag == 5:
                    _private_key, _private_padding = packet.unlock(self.passphrase)
                    # Don't really need the fingerprint, but we can use it to make it flexible
                    # to allow to retrieve the secret key either key_id or fingerprint
                    self.fingerprint = packet.fingerprint
                    self.key_id = packet.key_id
                    _tupled = self.retrieve_tuple(packet.pub_algorithm_type, _private_key.private_numbers())
                else:
                    packet.skip()

        return {'keyID': self.key_id, 'fingerprint': self.fingerprint, 'tuple': _tupled}


async def keystore(key_list, expiration=None):
    """A cache in-memory as a keystore. An expiration can be set in seconds."""
    start_time = time.time()
    objects = [PrivateKey(key_list[i][0], key_list[i][1]) for i in key_list]
    for obj in objects:
        obj.load_key()
        await cache.set(obj.key_id, obj.load_key(), ttl=expiration)

    LOG.info(f"Keystore loaded keys in: {(time.time() - start_time)} seconds ---")


def fingerprint_2key(requested_id):
    """Check if the key is a fingerprint or a regular key id."""
    if len(requested_id) > 16:
        key_id = requested_id[-16:]
    else:
        key_id = requested_id
    return key_id


@routes.get('/retrieve/{requested_id}')
async def retrieve_key(request):
    """Retrieve tuple to reconstruced unlocked key."""
    requested_id = request.match_info['requested_id']
    start_time = time.time()
    key_id = fingerprint_2key(requested_id)
    id_exists = await cache.exists(key_id)
    if id_exists:
        value = await cache.get(key_id)
        LOG.info(f"Retrived private key with id {key_id} in: {(time.time() - start_time)} seconds ---")
        return web.json_response(value)
    else:
        LOG.warn("Requested key {requested_id} not found.")
        return web.HTTPNotFound()


# REQUIRES AUTH
# WIP
@routes.get('/admin/unlock')
async def unlock_key(request):
    """Unlock key as it is about to expire."""
    await keystore(ACTIVE_KEYS, 86400)
    return web.HTTPCreated()


# Cache Profiling
# @routes.get('/admin/statistics')
# async def get_statistics(request):
#     """Return profiling statistics of the cache."""
#     return web.json_response(cache.profiling)


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

    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(ssl_certfile, ssl_keyfile)

    if not ssl_ctx:
        LOG.error('No SSL encryption. Exiting...')
    else:
        ssl_ctx = None
        LOG.info('With SSL encryption')

    for i, key in enumerate(KEYS.get('KEYS', 'active').split(",")):
        ls = [KEYS.get(key, 'PATH'), KEYS.get(key, 'PASSPHRASE')]
        ACTIVE_KEYS[i] = tuple(ls)

    host = CONF.get('keyserver', 'host')
    port = CONF.getint('keyserver', 'port')
    loop = asyncio.get_event_loop()

    # The keystore is good for 24h.
    loop.run_until_complete(keystore(ACTIVE_KEYS, 86400))

    keyserver = web.Application(loop=loop)
    keyserver.router.add_routes(routes)

    LOG.info("Start keyserver")
    web.run_app(keyserver, host=host, port=port, shutdown_timeout=0, loop=loop, ssl_context=ssl_ctx)


if __name__ == '__main__':
    main()
