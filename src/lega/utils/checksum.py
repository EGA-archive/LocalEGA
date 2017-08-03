# -*- coding: utf-8 -*-

import logging
import hashlib

from .exceptions import UnsupportedHashAlgorithm, CompanionNotFound

LOG = logging.getLogger('utils')

# Main map
_DIGEST = {
    'md5': hashlib.md5,
    'sha256': hashlib.sha256,
}

def instanciate(algo):
    try:
        return (_DIGEST[algo])()
    except KeyError:
        raise UnsupportedHashAlgorithm(algo)


def compute(f, m, bsize=8192):
    '''Computes the checksum of the bytes-like `f` using the message digest `m`.'''
    while True:
        data = f.read(bsize)
        if not data:
            break
        m.update(data)
    return m.hexdigest()

def is_valid(filepath, digest, hashAlgo = 'md5'):
    '''Verify the integrity of a file against a hash value'''

    assert( isinstance(digest,str) )

    m = instanciate(hashAlgo)

    with open(filepath, 'rb') as f: # Open the file in binary mode. No encoding dance.
        res = compute(f, m)
        LOG.debug('Calculated digest: '+res)
        LOG.debug('  Original digest: '+digest)
        return res == digest


def get_from_companion(filepath):
    '''Attempts to read a companion file.

    For each supported algorithms, we check if a companion file exists.
    If so, we read its content and return it, along with the selected current algorithm.

    We exit at the first one found and raise a CompanionNotFound exception in case none worked.
    '''
    for h in _DIGEST:
        companion = str(filepath) + '.' + h
        try:
            with open(companion, 'rt', encoding='utf-8') as f:
                return f.read(), h
        except OSError as e: # Not found, not readable, ...
            LOG.debug(f'Companion {companion}: {e!r}')
            # Check the next

    else: # no break statement was encountered
        raise CompanionNotFound(filepath)
