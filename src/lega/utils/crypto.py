#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Encryption/Decryption module
#
####################################
'''

import logging
import io
import os
import asyncio
import asyncio.subprocess
import hashlib
from pathlib import Path

from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES, PKCS1_OAEP

from ..conf import CONF
#from ..utils import cache_var
from .. import exceptions

HASH_ALGORITHMS = {
    'md5': hashlib.md5,
    'sha256': hashlib.sha256,
}

LOG = logging.getLogger('crypto')

def _master_key(key_nr=None, public=False):
    '''Fetch a RSA key from file'''
    if not key_nr:
        key_nr = CONF.getint('worker','active_key')
    domain = f'master.key.{key_nr}'
    LOG.debug(f"Fetching the RSA master key number {key_nr}")
    keyfile = CONF.get(domain,'pub_key' if public else 'key')
    passphrase = None if public else CONF.get(domain,'passphrase')
    LOG.debug(f"Fetching the RSA master key from {keyfile}")
    with open( keyfile, 'rb') as key_h:
        return RSA.import_key(key_h.read(), passphrase = passphrase)

def make_header(key_nr, enc_key_size, nonce_size, aes_mode):
    '''Create the header line for the re-encrypted files

    The header is simply of the form:
    Key number | Encryption key size (in bytes) | Nonce size | AES mode

    The key number points to a particular section of the configuration files, 
    holding the information about that key
    '''
    header = f'{key_nr}|{enc_key_size}|{nonce_size}|{aes_mode}\n'
    return header.encode('utf-8')

def from_header(h):
    '''Convert the given line into differents values, doing the opposite job as `make_header`'''
    header = bytearray()
    while True:
        b = h.read(1)
        if b in (b'\n', b''):
            break
        header.extend(b)

    LOG.debug(f'Found header: {header!r}')
    key_nr, enc_key_size, nonce_size, aes_mode, *rest = header.split(b'|')
    assert( not rest )
    return (int(key_nr),int(enc_key_size),int(nonce_size), aes_mode.decode())

def encrypt_engine():
    '''Generator that takes a block of data as input and encrypts it as output.

    The encryption algorithm is AES (in CTR mode), using a randomly-created session key.
    The session key is encrypted with RSA.
    '''

    LOG.info('Starting the cipher engine')
    session_key = get_random_bytes(32) # for AES-256
    LOG.debug(f'session key    = {session_key}')

    LOG.info('Creating AES cypher (CTR mode)')
    aes = AES.new(key=session_key, mode=AES.MODE_CTR)

    LOG.info('Creating RSA cypher')
    rsa = PKCS1_OAEP.new(_master_key(public=True)) # active_key

    encryption_key = rsa.encrypt(session_key)
    LOG.debug(f'\tencryption key = {encryption_key}')

    nonce = aes.nonce
    LOG.debug(f'AES nonce: {nonce}')

    clearchunk = yield (encryption_key, 'CTR', nonce)

    while True:
        clearchunk = yield aes.encrypt(clearchunk)
        # if clearchunk is None:
        #     LOG.info('Exiting the encryption engine')
        #     break # exit the generator

class ReEncryptor(asyncio.SubprocessProtocol):
    '''Re-encryption protocol.

    Each block of data received from the pipe is added to a buffer.
    When the buffer grows over a certain size `s`, the `s` first bytes of the buffer are re-encrypted using RSA/AES.

    We also calculate the checksum of the data received in the pipe.
    '''

    def __init__(self, hashAlgo, target_h, done):
        self.done = done
        self.errbuf = bytearray()
        self.engine = encrypt_engine()
        self.target_handler = target_h

        LOG.info(f'Setup {hashAlgo} digest')
        try:
            self.digest = (HASH_ALGORITHMS[hashAlgo])()
        except KeyError:
            raise ValueError(f'No support for the secure hashing algorithm: {hashAlgo}')

        LOG.info(f'Starting the encrypting engine')
        encryption_key, mode, nonce = next(self.engine)

        self.header = make_header(CONF.getint('worker','active_key'), len(encryption_key), len(nonce), mode)
    
        LOG.info(f'Writing header to file: {self.header[:-1]} (and enc key + nonce)')
        self.target_handler.write(self.header)
        self.target_handler.write(encryption_key)
        self.target_handler.write(nonce)

        LOG.info('Setup target digest')
        self.target_digest = hashlib.sha256()
        self.target_digest.update(self.header)
        self.target_digest.update(encryption_key)
        self.target_digest.update(nonce)

        # And now, daddy...
        super().__init__()

    def connection_made(self, transport):
        LOG.debug('Process started (PID: {})'.format(transport.get_pid()))
        self.transport = transport

    def pipe_data_received(self, fd, data):
        # Data is of size: 32768 or 65536 bytes 
        if not data:
            return
        if fd == 1:
            self._process_chunk(data)
        else: # If stderr (It should not be stdin)
            self.errbuf.extend(data) # f'Data on fd {fd}: {data}'

    def process_exited(self):
        # LOG.info('Closing the encryption engine')
        # self.engine.send(None) # closing it
        retcode = self.transport.get_returncode()
        stderr = self.errbuf.decode() if retcode else ''
        self.done.set_result( (retcode, stderr, self.digest.hexdigest()) ) # a tuple as one argument

    def _process_chunk(self,data):
        LOG.debug('processing {} bytes of data'.format(len(data)))
        self.digest.update(data)
        cipherchunk = self.engine.send(data)
        self.target_handler.write(cipherchunk)
        self.target_digest.update(cipherchunk)


def ingest(enc_file,
           org_hash,
           hash_algo,
           target):
    '''Decrypts a gpg-encoded file and verifies the integrity of its content.
       Finally, it re-encrypts it chunk-by-chunk'''

    assert( isinstance(org_hash,str) )

    cmd = CONF.get('worker','gpg_cmd',raw=True) % { 'file': enc_file }

    LOG.debug(f'Processing file\n'
              f'==============\n'
              f'enc_file  = {enc_file}\n'
              f'org_hash  = {org_hash}\n'
              f'hash_algo = {hash_algo}\n'
              f'target    = {target}\n'
              f'Decryption command: {cmd}')

    _err = None

    with open(target, 'wb') as target_h:

        loop = asyncio.get_event_loop()
        done = asyncio.Future(loop=loop)
        reencrypt_protocol = ReEncryptor(hash_algo, target_h, done)

        async def _re_encrypt():
            gpg_job = loop.subprocess_exec(lambda: reencrypt_protocol, cmd,
                                           stdin=None,
                                           stdout=asyncio.subprocess.PIPE,
                                           stderr=asyncio.subprocess.PIPE #stderr=asyncio.subprocess.DEVNULL # suppressing progress messages
            )
            transport, _ = await gpg_job
            await done
            transport.close()
            return done.result()

        gpg_result, gpg_error, calculated_digest = loop.run_until_complete(_re_encrypt())

        LOG.debug(f'Calculated digest: {calculated_digest}')
        LOG.debug(f'Compared to digest: {org_hash}')
        correct_digest = (calculated_digest == org_hash)
        
        if gpg_result != 0: # Swapped order on purpose
            _err = exceptions.GPGDecryption(gpg_result, gpg_error, enc_file)
            LOG.error(str(_err))
        if not correct_digest and not _err:
            _err = exceptions.Checksum(hash_algo,f'for decrypted content of {enc_file}')
            LOG.error(str(_err))

    if _err:
        LOG.warning(f'Removing {target}')
        os.remove(target)
        raise _err
    else:
        LOG.info(f'File encrypted')
        assert Path(target).exists()
        return (reencrypt_protocol.header, reencrypt_protocol.target_digest.hexdigest())

def chunker(stream, chunk_size=None):
    """Lazy function (generator) to read a stream one chunk at a time."""

    if not chunk_size:
        chunk_size = CONF.getint('worker','random_access_chunk_size',fallback=1 << 26) # 67 MB or 2**26

    assert(chunk_size >= 16)
    #assert(chunk_size % 16 == 0)
    LOG.debug(f'\tchunk size = {chunk_size}')
    yield chunk_size
    while True:
        data = stream.read(chunk_size)
        if not data:
            return None # No more data
        yield data

def decrypt_engine(encrypted_session_key, aes_mode, nonce, key_nr):

    LOG.info('Starting the decipher engine')

    LOG.info('Creating RSA cypher')
    rsa = PKCS1_OAEP.new(_master_key(key_nr, public=False))
    session_key = rsa.decrypt(encrypted_session_key)

    LOG.info(f'Creating AES cypher in mode {aes_mode}')
    aes = AES.new(key=session_key, mode=getattr(AES, 'MODE_' + aes_mode), nonce=nonce)

    LOG.info(f'Session key: {session_key}')
    LOG.info(f'Nonce: {nonce}')

    cipherchunk = yield

    while True:
        cipherchunk = yield aes.decrypt(cipherchunk)


def decrypt_from_vault( vault_filename,
                        org_hash,
                        hash_algo):

    try:
        h = HASH_ALGORITHMS.get(hash_algo)
    except KeyError:
        raise ValueError('No support for the secure hashing algorithm')
    else:
        digest = h()
        LOG.debug(f'Digest: {hash_algo}')

    with open(vault_filename, 'rb') as vault_source:

        LOG.debug('Decrypting file')
        key_nr, enc_key_size, nonce_size, aes_mode = from_header( vault_source )

        LOG.debug(f'encrypted_session_key (size): {enc_key_size}')
        LOG.debug(f'aes mode: {aes_mode}')
        
        encrypted_session_key = vault_source.read(enc_key_size)
        nonce = vault_source.read(nonce_size)
        
        engine = decrypt_engine( encrypted_session_key, aes_mode.upper(), nonce, key_nr )
        next(engine) # start it
        
        chunks = chunker(vault_source)
        next(chunks) # start it and ignore its return value
        
        for chunk in chunks:
            clearchunk = engine.send(chunk)
            digest.update(clearchunk)
                
        calculated_digest = digest.hexdigest()
        if calculated_digest != org_hash:
            LOG.debug('Invalid digest')
            LOG.debug(f'Calculated digest: {calculated_digest}')
            LOG.debug(f'Original digest: {org_hash}')
            raise VaultDecryption(vault_filename)
        else:
            LOG.debug(f'Valid digest')


# If that code is in a docker container, there is not much entropy
# so I don't know how good the key generation is
def generate_key(size):
    key = RSA.generate(size)
    seckey = key.exportKey('PEM').decode()
    pubkey = key.publickey().exportKey('OpenSSH').decode()
    return (pubkey,seckey)
