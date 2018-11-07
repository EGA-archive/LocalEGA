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
import io
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


import ed25519
from nacl.public import PrivateKey, PublicKey
from nacl.encoding import HexEncoder as KeyFormatter
#from nacl.encoding import URLSafeBase64Encoder as KeyFormatter
from crypt4gh.crypt4gh import Header
from aiohttp import web

from .conf import CONF, configure
from .utils import storage
from .utils import async_db as db

LOG = logging.getLogger(__name__)

####################################

async def init(app):
    # Some settings

    chunk_size = CONF.get_value('vault', 'chunk_size', conv=int, default=1<<22) # 4 MB
    app['chunk_size'] = chunk_size

    # Load the LocalEGA private key
    key_location = CONF.get_value('DEFAULT', 'private_key')
    LOG.info(f'Retrieving the Private Key from {key_location}')
    with open(key_location, 'rt') as k: # text file
        privkey = PrivateKey(k.read(), KeyFormatter)
        app['private_key'] = privkey

    # Load the LocalEGA header signing key
    signing_key_location = CONF.get_value('DEFAULT', 'signing_key')
    LOG.info(f'Retrieving the Signing Key from {signing_key_location}')
    if signing_key_location:
        with open(signing_key_location, 'rt') as k:  # hex file
            key_content = bytes.fromhex(k.read())
            print(key_content, len(key_content))
            app['signing_key'] = ed25519.SigningKey(key_content)
    else:
        app['signing_key'] = None


async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')
    app['db'].close()
    await app['db'].wait_closed()

####################################

# |-------------|--------------------------------------------------------|
# | Field       | Explanation                                            |
# |-------------|--------------------------------------------------------|
# | stable_id   | EGA stable id, in case we print a message              |
# | pubkey      | The public PGP key of the user for Crypt4GH encryption |
# |-------------|--------------------------------------------------------|

def request_context(func):
    async def wrapper(r):

        LOG.debug('Init Context')
        
        # Getting post data
        data = await r.json()
        LOG.debug('Data: %s', data)

        stable_id = data.get('stable_id')
        if not stable_id: # It should be there. Assertion instead?
            LOG.error('Missing stable ID')
            raise web.HTTPUnprocessableEntity(reason='Missing stable ID')
        
        pubkey = data.get('pubkey')
        if not pubkey: # It should be there. Assertion instead?
            LOG.error('Missing public key for the re-encryption')
            raise web.HTTPUnprocessableEntity(reason='Missing public key')
        # Load it
        pubkey = PublicKey(pubkey, KeyFormatter)

        request_id = None
        try:
            
            # Fetch information and Create request
            request_info = await db.make_request(stable_id)
            if not request_info:
                LOG.error('Unable to create a request entry')
                raise web.HTTPServiceUnavailable(reason='Unable to process request')
        
            # Request started
            request_id, header, vault_path, vault_type, _, _, _ = request_info
            
            # Set up file transfer type
            LOG.info('Loading the vault handler: %s', vault_type)
            if vault_type == 'S3':
                mover = storage.S3Storage()
            elif vault_type == 'POSIX':
                mover = storage.FileStorage()
            else:
                LOG.error('Invalid storage method: %s', vault_type)
                raise web.HTTPUnprocessableEntity(reason='Unsupported storage type')

            async def db_update(message):
                await db.update(request_id, status=message)

            # Do the job
            response, dlsize = await func(r,
                                          db_update,
                                          pubkey,
                                          r.app['private_key'],
                                          r.app['signing_key'],
                                          header,
                                          vault_path,
                                          mover,
                                          chunk_size=r.app['chunk_size'])
            # Mark as complete
            await db.download_complete(request_id, dlsize)
            return response
        #except web.HTTPError as err:
        except Exception as err:
            if isinstance(err,AssertionError):
                raise err
            cause = err.__cause__ or err
            LOG.error(f'{cause!r}') # repr = Technical
            if request_id:
                await db.set_error(request_id, cause, client_ip=data.get('client_ip'))
            raise web.HTTPServiceUnavailable(reason='Unable to process request')
    return wrapper


@request_context
async def outgest(r, set_progress, pubkey, privkey, signing_key, header, vault_path, mover, chunk_size=1<<22):

    # Crypt4GH encryption
    await set_progress('REENCRYPTING')
    LOG.info('Re-encrypting the header') # in hex -> bytes, and take away 16 bytes
    header_obj = Header.from_stream(io.BytesIO(bytes.fromhex(header)))
    reencrypted_header = header_obj.reencrypt(pubkey, privkey, signing_key=signing_key)
    renc_header = bytes(reencrypted_header)
    LOG.debug('Org header %s', header)
    LOG.debug('Reenc header %s', renc_header.hex())

    # Read the rest from the vault
    await set_progress('STREAMING')
    LOG.info('Opening vault file: %s', vault_path)
    with mover.open(vault_path, 'rb') as vfile:

        # Ready to answer
        response = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'application/octet-stream'})
        await response.prepare(r)
        # Sending the header
        await response.write(renc_header)
        await response.drain()
        bytes_count = len(renc_header)

        # Sending the remainder
        while True:
            data = vfile.read(chunk_size) # not async...I know
            if not data:
                break
            await response.write(data)
            await response.drain()
            bytes_count += len(data)

        # Finally
        await response.write_eof()
        return response, bytes_count

@configure
def main(args=None):

    host = CONF.get_value('DEFAULT', 'host')  # fallbacks are in defaults.ini
    port = CONF.get_value('DEFAULT', 'port', conv=int)

    #loop = asyncio.get_event_loop()
    #loop.set_debug(True)
    server = web.Application()
    server.router.add_post( '/', outgest)

    # Registering the initialization routine
    server.on_startup.append(init)
    server.on_cleanup.append(shutdown)

    # ...and cue music
    LOG.info(f"Start reencryption service on {host}:{port}")
    web.run_app(server, host=host, port=port)


if __name__ == '__main__':
    main()
