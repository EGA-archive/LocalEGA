# -*- coding: utf-8 -*-

'''
####################################
#
# Encryption/Decryption module
#
####################################
'''

import logging
import os
import asyncio
import asyncio.subprocess
from pathlib import Path
from hashlib import sha256

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from cryptography.hazmat.primitives import serialization

from . import exceptions, checksum

LOG = logging.getLogger('crypto')

###########################################################
# RSA Master Key
###########################################################
def get_rsa_private_key_material(content, password=None):
    assert( password is None or isinstance(password,str) )
    private_key = serialization.load_pem_private_key(
        content,
        password=None if password is None else password.encode(), # ok with empty password
        backend=default_backend()
    )
    private_material = private_key.private_numbers()
    public_material = private_material.public_numbers
    return {'public': { 'n': public_material.n,
                        'e': public_material.e},
            'private':{ 'd': private_material.d,
                        'p': private_material.p,
                        'q': private_material.q}
    }

def make_rsa_pubkey(material, backend):
    public_material = material['public']
    n = public_material['n'] # Note: all the number are already int
    e = public_material['e']
    return rsa.RSAPublicNumbers(e,n).public_key(backend)

def make_rsa_privkey(material, backend):
    public_material = material['public']
    private_material = material['private']
    n = public_material['n']  # Note: all the number are already int
    e = public_material['e']
    d = private_material['d']
    p = private_material['p']
    q = private_material['q']
    pub = rsa.RSAPublicNumbers(e,n)
    dmp1 = rsa.rsa_crt_dmp1(d, p)
    dmq1 = rsa.rsa_crt_dmq1(d, q)
    iqmp = rsa.rsa_crt_iqmp(p, q)
    return rsa.RSAPrivateNumbers(p, q, d, dmp1, dmq1, iqmp, pub).private_key(backend)


def serialize_rsa_private_key(content, password=None):
    assert( password is None or isinstance(password,str) )
    private_key = serialization.load_pem_private_key(
        content,
        password=None if password is None else password.encode(), # ok with empty password
        backend=default_backend()
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

###########################################################
# Ingestion
###########################################################

def make_header(key_id, enc_key_size, nonce_size):
    '''Create the header line for the re-encrypted files

    The header is simply of the form:
    Key ID | Encryption key size (in bytes) | Nonce size

    The key number points to a particular section of the configuration files, 
    holding the information about that key
    '''
    return f'{key_id}|{enc_key_size}|{nonce_size}|CTR'

def encrypt_engine(master_key):
    '''Generator that takes a block of data as input and encrypts it as output.

    The encryption algorithm is AES (in CTR mode), using a randomly-created session key.
    The session key is encrypted with RSA.
    '''

    LOG.info('Starting the cipher engine')
    session_key = os.urandom(32) # for AES-256
    LOG.debug(f'session key    = {session_key}')

    nonce = os.urandom(16)
    LOG.debug(f'CTR nonce: {nonce}')

    LOG.info('Creating AES cypher (CTR mode)')
    backend = default_backend()
    cipher = Cipher(algorithms.AES(session_key), modes.CTR(nonce), backend=backend)
    aes = cipher.encryptor()

    LOG.info('Encrypting the session key with RSA')
    rsa_key = make_rsa_pubkey(master_key, backend)
    LOG.debug(f'\trsa key size = {rsa_key.key_size}')
    encryption_key = rsa_key.encrypt(session_key,
                                     padding.OAEP(
                                         mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                         algorithm=hashes.SHA256(),
                                         label=None))
    LOG.debug(f'\tencryption key = {encryption_key}')

    clearchunk = yield (encryption_key, nonce)
    while True:
        if clearchunk is None:
            yield bytes(aes.finalize()) # instead of return
        else:
            clearchunk = yield bytes(aes.update(clearchunk))

class ReEncryptor(asyncio.SubprocessProtocol):
    '''Re-encryption protocol.

    Each block of data received from the pipe is added to a buffer.
    When the buffer grows over a certain size `s`, the `s` first bytes of the buffer are re-encrypted using RSA/AES.

    We also calculate the checksum of the data received in the pipe.
    '''

    def __init__(self, master_key, hashAlgo, target_h, done):
        self.done = done
        self.errbuf = bytearray()
        self.engine = encrypt_engine(master_key)
        self.target_handler = target_h

        LOG.info(f'Setup {hashAlgo} digest')
        self.digest = checksum.instantiate(hashAlgo)

        LOG.info(f'Starting the encrypting engine')
        encryption_key, nonce = next(self.engine)

        self.header = make_header(master_key['id'], len(encryption_key), len(nonce))
        header_b = self.header.encode()
        
        LOG.info(f'Writing header {self.header} to file, followed by encrypting key and nonce')
        self.target_handler.write(header_b)
        self.target_handler.write(b'\n')
        self.target_handler.write(encryption_key) # encrypted session key first
        self.target_handler.write(nonce)          # nonce then
        
        LOG.info('Setup target digest')
        self.target_digest = sha256()
        self.target_digest.update(header_b)
        self.target_digest.update(b'\n')
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
        LOG.info('Closing the encryption engine')
        self._finalize() # flushing the engine
        retcode = self.transport.get_returncode()
        stderr = self.errbuf.decode() if retcode else ''
        self.done.set_result( (retcode, stderr, self.digest.hexdigest()) ) # a tuple as one argument

    def _process_chunk(self,data):
        LOG.debug(f'processing {len(data)} bytes of data')
        self.digest.update(data)
        cipherchunk = self.engine.send(data)
        self.target_handler.write(cipherchunk)
        self.target_digest.update(cipherchunk)

    def _finalize(self):
        LOG.debug(f'Finalizing stream of data')
        cipherchunk = self.engine.send(None)
        if cipherchunk:
            LOG.debug(f'Flushed {len(cipherchunk)} bytes of data from the engine')
            self.target_handler.write(cipherchunk)
            self.target_digest.update(cipherchunk)


def ingest(decrypt_cmd,
           enc_file,
           org_hash, hash_algo,
           master_key,
           target):
    '''Decrypts a gpg-encoded file and verifies the integrity of its content.
       Finally, it re-encrypts it chunk-by-chunk'''

    LOG.debug(f'Processing file\n'
              f'==============\n'
              f'enc_file  = {enc_file}\n'
              f'org_hash  = {org_hash}\n'
              f'hash_algo = {hash_algo}\n'
              f'target    = {target}\n')

    assert( isinstance(org_hash,str) )

    _err = None
    cmd = decrypt_cmd.split(None) # whitespace split

    with open(target, 'wb') as target_h:

        loop = asyncio.get_event_loop()
        done = asyncio.Future(loop=loop)
        reencrypt_protocol = ReEncryptor(master_key, hash_algo, target_h, done)

        LOG.debug(f'Spawning a separate process running: {cmd}')

        async def _re_encrypt():
            gpg_job = loop.subprocess_exec(lambda: reencrypt_protocol, *cmd, # must pass an argument list, not a single string
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
            _err = exceptions.Checksum(hash_algo, file=enc_file, decrypted=True)
            LOG.error(str(_err))

    if _err is not None:
        LOG.warning(f'Removing {target}')
        os.remove(target)
        raise _err
    else:
        LOG.info(f'File encrypted')
        assert Path(target).exists()
        return (reencrypt_protocol.header, reencrypt_protocol.target_digest.hexdigest())



###########################################################
# Decryption code
###########################################################
def chunker(stream, chunk_size=None):
    """Lazy function (generator) to read a stream one chunk at a time."""

    chunk_size = 1 << 10
    yield chunk_size
    while True:
        data = stream.read(chunk_size)
        if not data:
            return None # No more data
        yield data

def from_header(h):
    '''Convert the given line into differents values, doing the opposite job as `make_header`'''
    header = bytearray()
    while True:
        b = h.read(1)
        if b in (b'\n', b''):
            break
        header.extend(b)

    header = header.decode()
    LOG.debug(f'Found header: {header}')
    key_id, session_key_size, nonce_size, aes_mode = header.split('|')
    assert( aes_mode == 'CTR' )
    return (key_id, int(session_key_size), int(nonce_size))

def decrypt_engine( session_key, nonce, backend ):

    LOG.info('Starting the decryption engine')
    cipher = Cipher(algorithms.AES(session_key), modes.CTR(nonce), backend=backend)
    aes = cipher.decryptor()

    cipherchunk = yield 
    while True:
        if cipherchunk is None:
            yield bytes(aes.finalize()) # instead of return
        else:
            cipherchunk = yield bytes(aes.update(cipherchunk))


def decrypt_from_vault(infile, master_key, outfile=None, hasher=None):

    LOG.debug('Decrypting file')
    key_id, session_key_size, nonce_size = from_header( infile )

    encrypted_session_key = infile.read(session_key_size)
    nonce = infile.read(nonce_size)

    # LOG.debug(f'encrypted_session_key: {encrypted_session_key.hex()}')
    # LOG.debug(f'nonce_key: {nonce.hex()}')

    LOG.info('Decrypting the session key with RSA')
    backend = default_backend()
    rsa_key = make_rsa_privkey(master_key, backend)
    LOG.debug(f'\trsa key size = {rsa_key.key_size}')
    session_key = rsa_key.decrypt(encrypted_session_key,
                                  padding.OAEP(
                                      mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                      algorithm=hashes.SHA256(),
                                      label=None))
    LOG.debug(f'\tsession key = {session_key}')
    
    engine = decrypt_engine( session_key, nonce, backend )
    next(engine) # start it

    chunks = chunker(infile) # the rest
    next(chunks) # start it and ignore its return value

    for chunk in chunks:
        clearchunk = engine.send(chunk)
        if outfile:
            outfile.write(clearchunk)
        if hasher:
            hasher.update(clearchunk)

    # finally, flushing
    clearchunk = engine.send(None)
    if clearchunk and outfile:
        outfile.write(clearchunk)
    if clearchunk and hasher:
        hasher.update(clearchunk)
