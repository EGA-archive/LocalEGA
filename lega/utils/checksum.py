# -*- coding: utf-8 -*-
"""Computes the checksum."""

import logging
import hashlib

from .exceptions import UnsupportedHashAlgorithm, CompanionNotFound

LOG = logging.getLogger(__name__)

# Main map
_DIGEST = {
    'md5': hashlib.md5,
    'sha256': hashlib.sha256,
}


def supported_algorithms():
    """Supported hashing algorithms, currently ``md5`` and ``sha256``."""
    return tuple(_DIGEST.keys())


def instantiate(algo):
    """Instantiate algorithm."""
    try:
        return (_DIGEST[algo])()
    except KeyError:
        raise UnsupportedHashAlgorithm(algo)


def calculate(filepath, algo, bsize=8192):
    """Compute the checksum of a file using the message digest ``m``."""
    try:
        m = instantiate(algo)
        with open(filepath, 'rb') as f:  # Open the file in binary mode. No encoding dance.
            while True:
                data = f.read(bsize)
                if not data:
                    break
                m.update(data)
        return m.hexdigest()
    except OSError as e:
        LOG.error('Unable to calculate checksum: %r', e)
        return None


def is_valid(filepath, digest, hashAlgo='md5'):
    """Verify the integrity of a file against a hash value."""
    assert(isinstance(digest, str))

    res = calculate(filepath, hashAlgo)
    LOG.debug('Calculated digest: '+res)
    LOG.debug('  Original digest: '+digest)
    return res is not None and res == digest


def get_from_companion(filepath):
    """Attempt to read a companion file.

    For each supported algorithms, we check if a companion file exists.
    If so, we read its content and return it, along with the selected current algorithm.

    We exit at the first one found and raise a CompanionNotFound exception in case none worked.
    """
    for h in _DIGEST:
        companion = str(filepath) + '.' + h
        try:
            with open(companion, 'rt', encoding='utf-8') as f:
                return f.read(), h
        except OSError as e:  # Not found, not readable, ...
            LOG.debug('Companion %s: %r', companion, e)
            # Check the next

    else:  # no break statement was encountered
        raise CompanionNotFound(filepath)
