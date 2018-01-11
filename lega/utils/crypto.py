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


from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES, PKCS1_OAEP

from . import exceptions, checksum, get_file_content

LOG = logging.getLogger('crypto')

###########################################################
# Ingestion
###########################################################

def make_header(key_nr, enc_key_size, nonce_size, aes_mode):
    '''Create the header line for the re-encrypted files

    The header is simply of the form:
    Key number | Encryption key size (in bytes) | Nonce size | AES mode

    The key number points to a particular section of the configuration files, 
    holding the information about that key
    '''
    return f'{key_nr}|{enc_key_size}|{nonce_size}|{aes_mode}'

def encrypt_engine(key,passphrase=None):
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
    rsa_key = RSA.import_key(key, passphrase = passphrase)
    rsa = PKCS1_OAEP.new(rsa_key)

    encryption_key = rsa.encrypt(session_key)
    LOG.debug(f'\tencryption key = {encryption_key}')

    nonce = aes.nonce
    LOG.debug(f'AES nonce: {nonce}')

    clearchunk = yield (encryption_key, 'CTR', nonce)
    while True:
        clearchunk = yield aes.encrypt(clearchunk)


class ReEncryptor(asyncio.SubprocessProtocol):
    '''Re-encryption protocol.

    Each block of data received from the pipe is added to a buffer.
    When the buffer grows over a certain size `s`, the `s` first bytes of the buffer are re-encrypted using RSA/AES.

    We also calculate the checksum of the data received in the pipe.
    '''

    def __init__(self, active_key, master_pubkey, hashAlgo, target_h, done):
        self.done = done
        self.errbuf = bytearray()
        self.engine = encrypt_engine(master_pubkey) # pubkey => no passphrase
        self.target_handler = target_h

        LOG.info(f'Setup {hashAlgo} digest')
        self.digest = checksum.instantiate(hashAlgo)

        LOG.info(f'Starting the encrypting engine')
        encryption_key, mode, nonce = next(self.engine)

        self.header = make_header(active_key, len(encryption_key), len(nonce), mode)
        header_b = self.header.encode()
        
        LOG.info(f'Writing header {self.header} to file, followed by encrypting key and nonce')
        self.target_handler.write(header_b)
        self.target_handler.write(b'\n')
        self.target_handler.write(encryption_key)
        self.target_handler.write(nonce)
        
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


def ingest(gpg_cmd,
           enc_file,
           org_hash, hash_algo,
           active_key, master_key,
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
    cmd = gpg_cmd.split(None) # whitespace split

    with open(target, 'wb') as target_h:

        loop = asyncio.get_event_loop()
        done = asyncio.Future(loop=loop)
        reencrypt_protocol = ReEncryptor(active_key, master_key, hash_algo, target_h, done)

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
