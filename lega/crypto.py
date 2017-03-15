# https://wiki.gnupg.org/APIs
# https://wiki.python.org/moin/GnuPrivacyGuard

import logging
import io

import gpg
from gpg.constants import PROTOCOL_OpenPGP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256

from lega.conf import CONF
from lega import checksum

LOG = logging.getLogger(__name__)

## GnuPG
GPG_CONTEXT = None
## RSA
MASTER_KEY = None

CHUNK_SIZE = 1 << 26 # 67 MB or 2**26

def setup():
    global GPG_CONTEXT
    global MASTER_KEY
    global CHUNK_SIZE

    if GPG_CONTEXT is None:
        GPG_CONTEXT = gpg.Context(
            armor    = CONF.getboolean('worker','armor',fallback=False)
        )
        GPG_CONTEXT.set_engine_info(
            gpg.constants.PROTOCOL_OpenPGP, # protocol
            home_dir = CONF.get('worker','gpg_home')
        )
        GPG_CONTEXT.set_status_cb(lambda x,y: LOG.debug('{} {}'.format(x,y)))
        # def passphrase_cb(hint, desc, prev_bad, hook):
        #     return CONF.get('worker','gpg_passphrase')
        # GPG_CONTEXT.set_passphrase_cb(passphrase_cb)


    if MASTER_KEY is None:
        with open( CONF.get('worker','master_pub_key'), 'rb') as pubkey:
            MASTER_KEY = RSA.import_key(pubkey.read(),
                                        passphrase = CONF.get('worker','master_key_passphrase'))

    CHUNK_SIZE = CONF.getint('worker','random_access_chunk_size',fallback=CHUNK_SIZE)
    assert(CHUNK_SIZE % 16 == 0)


def re_encrypt( stream, target ):

    session_key = get_random_bytes(32) # for AES-256
    LOG.debug('session key    = {}'.format(session_key))

    LOG.debug('Creating AES cypher')
    iv = get_random_bytes(AES.block_size) # 16 bytes
    aes = AES.new(key=session_key, mode=AES.MODE_CBC,iv=iv)

    LOG.debug('Creating RSA cypher')
    rsa = PKCS1_OAEP.new(MASTER_KEY, hashAlgo=SHA256)

    encryption_key = rsa.encrypt(session_key)
    LOG.debug('\tencryption key = {}\n' \
              '\tchunk size     = {}'.format(encryption_key,CHUNK_SIZE))

    with open(target, 'wb') as target_h:

        LOG.debug('Writing header to file')
        header = "# Key length: {} | AES mode: CBC | AES block size: {}\n".format(len(encryption_key), aes.block_size)
        target_h.write(header.encode('utf-8'))
        LOG.debug('Writing key to file')
        target_h.write(encryption_key)
        LOG.debug('Writing cipher header to file')
        cipherheader = '\n# ciphertext (chunk size: {})\n'.format(CHUNK_SIZE)
        target_h.write(cipherheader.encode('utf-8'))

        LOG.debug('Writing blocks to file')
        padding = None
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if len(chunk) == 0:
                LOG.debug('no more data')
                break
            elif len(chunk) % 16 != 0:
                LOG.debug('Must pad the block: {}'.format(len(chunk) % 16))
                padding = b' ' * (16 - len(chunk) % 16)
                chunk += padding

            cipherchunk = aes.encrypt(chunk)
            target_h.write(cipherchunk)

        LOG.debug('File ingested')
        if padding:
            paddingheader = '\n#Padding size: {}'.format(len(padding))
            target_h.write(paddingheader.encode('utf-8'))


def ingest(enc_file,
           org_hash,
           hash_algo,
           target
):
    '''Decrypts a gpg-encoded file and verifies the integrity of its content.
Finally, it re-encrypts it chunk-by-chunk'''

    assert( isinstance(org_hash,str) )

    #return ('File: {} and {}: {}'.format(filepath, hashAlgo, filehash))
    LOG.debug('Processing file\n==============\n' \
              'enc_file  = {}\n' \
              'org_hash  = {}\n' \
              'hash_algo = {}\n' \
              'target    = {}'.format(enc_file,org_hash,hash_algo,target))

    # Open the file in binary mode. No encoding dance.
    with open(enc_file, 'rb') as enc_file_h:

        ################# Decrypting using GPG
        LOG.debug('GPG Decrypting: {}'.format(enc_file))
        decrypted_content, _, _ = GPG_CONTEXT.decrypt(enc_file_h, verify=False) # passphrase is in gpg-agent

        ################# Check integrity of decrypted content
        LOG.debug('Verifying the {} checksum of decrypted content for file: {}'.format(hash_algo, enc_file))

        decrypted_stream = io.BytesIO(decrypted_content)
        if not checksum.verify(decrypted_stream, org_hash, hashAlgo = hash_algo):
            errmsg = 'Invalid {} checksum for the decrypted content of {}'.format(hash_algo, enc_file)
            LOG.debug(errmsg)
            raise Exception(errmsg)

        LOG.debug('Valid {} checksum'.format(hash_algo))

        ################# Re-encrypt the file
        LOG.debug('Re-encrypting into {}'.format(target))
        decrypted_stream.seek(0)
        re_encrypt(decrypted_stream, target)

        return 0


# def encrypt(in_filename, out_filename = None):
#     '''Encrypts a file using the Master Private Key'''

#     if not out_filename:
#         out_filename = in_filename + '.gpg'

#     LOG.debug('''Encryption: Input file: {}\nEncryption: Output file: {}'''.format(in_filename,out_filename))

#     # Open the file in binary mode. No encoding dance.
#     with open(in_filename, 'rb') as input_file:
#         ciphertext,_,_ = GPG_CONTEXT.encrypt(input_file.read(), [MASTER_KEY], compress=CONF.getboolean('worker','compress',fallback=True))

#         if out_filename:
#             with open(out_filename, 'wb') as output_file:
#                 output_file.write(ciphertext)

#         return ciphertext

# def gpg_decrypt(ciphertext):
#     '''Decrypts a string using the GPG Key'''
#     assert( GPG_CONTEXT is not None )
#     plaintext,_,_ = GPG_CONTEXT.decrypt(ciphertext, verify = False)
#     return plaintext
