#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Encryption/Decryption module
#
####################################
'''
# https://wiki.gnupg.org/APIs
# https://wiki.python.org/moin/GnuPrivacyGuard

import logging
import io
import os

import gpg
from gpg.constants import PROTOCOL_OpenPGP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256

from .conf import CONF
from . import checksum
from .utils import cache_var

LOG = logging.getLogger('crypto')

@cache_var('MASTER_KEY')
def _master_key():
    '''Fetch the RSA master key from file'''
    keyfile = CONF.get('worker','master_pub_key')
    LOG.debug(f"Fetching the RSA master key from {keyfile}")
    with open( keyfile, 'rb') as pubkey:
        return RSA.import_key(pubkey.read(),
                              passphrase = CONF.get('worker','master_key_passphrase'))

@cache_var('GPG_CONTEXT')
def _gpg_ctx():
    '''Create the GPG context'''
    LOG.debug("Creating the GPG context")
    homedir = CONF.get('worker','gpg_home')
    armor   = CONF.getboolean('worker','gpg_armor',fallback=False)
    offline = CONF.getboolean('worker','gpg_offline',fallback=False)
    LOG.debug(f"\thomedir: {homedir}\n\tarmor: {armor}\n\toffline: {offline}")
    ctx = gpg.Context(armor=armor, offline=offline)
    ctx.set_engine_info(gpg.constants.PROTOCOL_OpenPGP, home_dir=homedir)
    ctx.set_status_cb(lambda x,y: LOG.debug(f'{x!r} {y!r}'))
    return ctx

def chunker(stream, chunk_size=None):
    """Lazy function (generator) to read a file one chunk at a time."""

    if not chunk_size:
        chunk_size = CONF.getint('worker','random_access_chunk_size',fallback=1 << 26) # 67 MB or 2**26

    assert(chunk_size >= 16)
    #assert(chunk_size % 16 == 0)
    LOG.debug(f'\tchunk size     = {chunk_size}')
    yield chunk_size
    while True:
        data = stream.read(chunk_size)
        if not data:
            return None # No more data
        yield data

def encrypt_engine(padding_character=None):

    if not padding_character:
        padding_character = b' '

    LOG.info('Starting the cipher engine')
    session_key = get_random_bytes(32) # for AES-256
    LOG.debug(f'session key    = {session_key}')

    LOG.info('Creating AES cypher (CTR mode)')
    aes = AES.new(key=session_key, mode=AES.MODE_CTR)

    LOG.info('Creating RSA cypher')
    rsa = PKCS1_OAEP.new(_master_key(), hashAlgo=SHA256)

    encryption_key = rsa.encrypt(session_key)
    LOG.debug(f'\tencryption key = {encryption_key}')

    chunk = yield (encryption_key, 'CTR', aes.block_size)

    while True:
        chunk_mod_16 = len(chunk) % 16
        padding = None
        if chunk_mod_16 != 0:
            LOG.debug(f'Must pad the block: {chunk_mod_16}')
            padding = padding_character * (16 - chunk_mod_16)
            chunk += padding

        chunk = yield (aes.encrypt(chunk),padding)


def re_encrypt( stream, target ):
    try:
        with open(target, 'wb') as target_h:

            engine = encrypt_engine()
            chunks = chunker(stream)

            encryption_key, mode, block_size = next(engine)
            chunk_size = next(chunks)

            header = f'{len(encryption_key)}|{mode}|{block_size}|{chunk_size}'
            LOG.info(f'Writing header to file: {header}')
            target_h.write(header.encode('utf-8'))
            target_h.write(b'\n')

            LOG.info('Writing key to file')
            target_h.write(encryption_key)

            LOG.info('Writing blocks to file')
            for chunk in chunks:
                cipherchunk, padding = engine.send(chunk)
                target_h.write(cipherchunk)
                if padding:
                    LOG.debug('Padding size: {len(padding)}')
                    target_h.write(f'\n#Padding size: {len(padding)}'.encode('utf-8'))

        LOG.debug('File re-encrypted')
        return 0
    except Exception as e:
        LOG.warning(f'{e!r}')
        LOG.warning(f'Removing {target}')
        os.remove(target)
        return 1

def ingest(enc_file,
           org_hash,
           hash_algo,
           target
):
    '''Decrypts a gpg-encoded file and verifies the integrity of its content.
       Finally, it re-encrypts it chunk-by-chunk'''

    assert( isinstance(org_hash,str) )

    #return ('File: {} and {}: {}'.format(filepath, hashAlgo, filehash))
    LOG.debug(f'Processing file\n==============\n'
              f'enc_file  = {enc_file}\n'
              f'org_hash  = {org_hash}\n'
              f'hash_algo = {hash_algo}\n'
              f'target    = {target}')

    # Open the file in binary mode. No encoding dance.
    with open(enc_file, 'rb') as enc_file_h:

        ################# Decrypting using GPG
        LOG.debug(f'GPG Decrypting: {enc_file}')
        decrypted_content, _, _ = _gpg_ctx().decrypt(enc_file_h, verify=False) # passphrase is in gpg-agent

        ################# Check integrity of decrypted content
        LOG.debug(f'Verifying the {hash_algo} checksum of decrypted content of {enc_file}')

        decrypted_stream = io.BytesIO(decrypted_content)
        if not checksum.verify(decrypted_stream, org_hash, hashAlgo = hash_algo):
            errmsg = f'Invalid {hash_algo} checksum for decrypted content of {enc_file}'
            LOG.debug(errmsg)
            raise Exception(errmsg)

        LOG.debug(f'Valid {hash_algo} checksum')

        ################# Re-encrypt the file
        LOG.debug(f'Re-encrypting into {target}')
        decrypted_stream.seek(0)
        return re_encrypt(decrypted_stream, target)

if __name__ == '__main__':
    import sys
    CONF.setup(sys.argv[1:]) # re-conf

    stream = io.BytesIO(b'Hello ' * 2048)

    re_encrypt( stream, 'res.enc' )
