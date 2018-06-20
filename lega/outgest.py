#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Decrypting file from the vault, given a stable ID.
#
# Only used for testing to see if the encrypted file can be sent as a Crypt4GH-formatted stream
#
####################################
'''

import sys
import os
import logging
from urllib.request import urlopen
#import tempfile
import json
import ssl
from functools import wraps
from urllib.request import urlopen
from urllib.error import HTTPError
from pathlib import Path
import asyncio

from aiohttp import web
import jinja2
import aiohttp_jinja2
import pgpy
from legacryptor.crypt4gh import get_key_id, reencrypt_header, cryptor, header_to_records
import psycopg2

from .conf import CONF
from .utils import db, exceptions, storage

LOG = logging.getLogger(__name__)

####################################

# def fake_guard(async_func):
#     '''Decorator restrain endpoint access to only Central EGA'''
#     @wraps(async_func)
#     async def wrapper(request):
#         # Just an example
#         if request.headers.get('X-LEGA-OUTGEST', 'no') != 'yes':
#             raise HTTPUnauthorized(text='Not authorized. You should be eligible for LocalEGA outgestion.\n')
#         # Otherwise, it is from CentralEGA, we continue
#         res = async_func(request)
#         res.__name__ = getattr(async_func, '__name__', None)
#         res.__qualname__ = getattr(async_func, '__qualname__', None)
#         return (await res)
#     return wrapper

# Not async but...äschh...
# put your dirty hands in the database
async def get_info(conn, stable_id):
    try:
        with (await conn.cursor()) as cur:
            query = 'SELECT vault_path, header FROM files WHERE stable_id = %(stable_id)s;'
            await cur.execute(query, { 'stable_id': stable_id})
            return await cur.fetchone()
    except psycopg2.InternalError as pgerr:
        LOG.debug(f'Info for {stable_id}: {pgerr!r}')
        return None


def go_go_gadget_reencrypted_header(enc_header, pubkey):
    keyid = get_key_id(enc_header)
    LOG.info(f'Key ID {keyid}')
    keyurl = CONF.get_value('outgestion', 'keyserver_endpoint', raw=True) % keyid
    verify = CONF.get_value('outgestion', 'verify_keyserver_certificate', conv=bool)
    LOG.info(f'Retrieving the Private Key from {keyurl} (verify certificate: {verify})')

    if verify:
        ctx=None # nothing to be done: done by default in urlopen
    else: # no verification
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        with urlopen(keyurl, context=ctx) as response:
            privkey,_ = pgpy.PGPKey.from_blob(response.read())
            with privkey.unlock(os.environ['LEGA_PASSWORD']) as seckey:
                return reencrypt_header(pubkey, seckey, enc_header)
    except HTTPError as e:
        LOG.error(e)
        msg = str(e)
        if e.code == 404: # If key not found, then probably wrong key.
            raise exceptions.PGPKeyError(msg)
        # Otherwise
        raise exceptions.KeyserverError(msg)
    except Exception as e:
        raise exceptions.KeyserverError(str(e))

def get_records(header):
    keyid = get_key_id(header)
    LOG.info(f'Key ID {keyid}')
    keyurl = CONF.get_value('outgestion', 'keyserver_endpoint', raw=True) % keyid
    verify = CONF.get_value('outgestion', 'verify_certificate', conv=bool)
    LOG.info(f'Retrieving the Private Key from {keyurl} (verify certificate: {verify})')

    if verify:
        ctx=None # nothing to be done: done by default in urlopen
    else: # no verification
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        with urlopen(keyurl, context=ctx) as response:
            privkey = response.read()
            return header_to_records(privkey, header, os.environ['LEGA_PASSWORD'])
    except HTTPError as e:
        LOG.error(e)
        msg = str(e)
        if e.code == 404: # If key not found, then probably wrong key.
            raise exceptions.PGPKeyError(msg)
        # Otherwise
        raise exceptions.KeyserverError(msg)
    except Exception as e:
        raise exceptions.KeyserverError(str(e))

####################################

@aiohttp_jinja2.template('outgest.html')
async def index(request):
    '''Main endpoint
    The template is `outgest.html` in the configured template folder.
    '''
    return { 'country': 'Sweden' }

#@fake_guard
async def outgest(request):

    data = await request.post()

    if not data:
        raise web.HTTPBadRequest(text='POST data required')

    LOG.info('Data: %s', data)

    stable_id = data['stable_id']
    LOG.info('Requested Stable ID: %s', stable_id)

    pk = data['pubkey']
    pubkey,_ = pgpy.PGPKey.from_blob(pk.file.read())
    LOG.info('Got the following pubkey\n%s', str(pubkey))

    response = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'application/octet-stream'})
    await response.prepare(request)

    LOG.info('Get the file mapping for stable id: %s', stable_id)
    info = await get_info(request.app['db'], stable_id)
    if not info:
        raise web.HTTPBadRequest(text='Unkown file mapping')
    vault_path, header = info
    encrypted_part = bytes.fromhex(header)[16:] # in hex -> bytes, and take away 16 bytes

    LOG.info('Opening vault file: %s', vault_path)
    chunk_size = request.app['chunk_size']
    mover = request.app['storage']

    do_encryption = data['encrypt'] == 'True'
    LOG.info('Encryption requested: %s', do_encryption)

    if do_encryption:
        LOG.info('Re-encrypting the header')
        reencrypted_header = go_go_gadget_reencrypted_header(encrypted_part, pubkey)
        LOG.info('Org header %s', header)
        LOG.info('Reenc header %s', reencrypted_header.hex())
        await response.write(reencrypted_header)
        await response.drain()

        LOG.info('Opening vault file: %s', vault_path)
        chunk_size = request.app['chunk_size']
        mover = request.app['storage']
        with mover.open(vault_path, 'rb') as infile:
            while True:
                data = infile.read(chunk_size) # not async...I know
                if not data:
                    break
                await response.write(data)
                await response.drain()

    else:
        # Get it from the header and the keyserver
        records = get_records(encrypted_part) # might raise exception
        r = records[0] # only first one
        LOG.info('Record %s', r)

        with mover.open(vault_path, 'rb') as infile:
            LOG.debug("Shifting to right cipher position")
            orgmdc = infile.read(32)
            # r.ciphertext_start -= 32
            # infile.seek(r.ciphertext_start,io.SEEK_CUR)
    
            LOG.debug("Streaming content")
            engine = cryptor(r.session_key, r.iv, method='decryptor')
            next(engine)

            chunk1 = infile.read(chunk_size)
            while True:
                await response.write(engine.send(chunk1))
                await response.drain()
                chunk2 = infile.read(chunk_size)
                if not chunk2: # Finally, if chunk2 is empty
                    final_data = engine.send(None)
                    await response.write(final_data)
                    await response.drain()
                    break
                chunk1 = chunk2 # Move chunk2 to chunk1, and let it read a new chunk2

    # Finally
    await response.write_eof()
    return response

async def init(app):
    '''Initialization running before the loop.run_forever'''
    app['db'] = await db.create_pool(loop=app.loop)
    LOG.info('DB Connection pool created')

    store = getattr(storage, CONF.get_value('vault', 'driver', default='FileStorage'))
    app['storage'] = store()
    chunk_size = CONF.get_value('vault', 'chunk_size', conv=int, default=1<<22) # 4 MB
    app['chunk_size'] = chunk_size
    LOG.info('Backend storage connection initialized')


async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')
    app['db'].close()
    await app['db'].wait_closed()

def main(args=None):
    print("====== JUST FOR TESTING =======", file=sys.stderr)
    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    host = CONF.get_value('outgestion', 'host')  # fallbacks are in defaults.ini
    port = CONF.get_value('outgestion', 'port', conv=int)

    ssl_certfile = Path(CONF.get_value('outgestion', 'ssl_certfile')).expanduser()
    ssl_keyfile = Path(CONF.get_value('outgestion', 'ssl_keyfile')).expanduser()
    LOG.debug(f'Certfile: {ssl_certfile}')
    LOG.debug(f'Keyfile: {ssl_keyfile}')
    sslcontext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    sslcontext.check_hostname = False
    sslcontext.load_cert_chain(ssl_certfile, ssl_keyfile)


    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    server = web.Application(loop=loop)

    # Where the templates are
    template_loader = jinja2.FileSystemLoader(str(Path(__file__).parent / 'conf' / 'templates'))
    aiohttp_jinja2.setup(server, loader=template_loader)

    server.router.add_get( '/', index)
    server.router.add_post( '/', outgest)

    # Registering some initialization and cleanup routines
    LOG.info('Setting up callbacks')
    server.on_startup.append(init)
    server.on_shutdown.append(shutdown)

    LOG.info(f"Start outgest server on {host}:{port}")
    web.run_app(server, host=host, port=port, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()

