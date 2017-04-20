# -*- coding: utf-8 -*-

'''
Supported algorithms: MD5 and SHA256

We will read the files in chunks of n bytes, where n is:
* 128 * 64 for MD5
* 256 * 64 for SHA256
'''

import hashlib
import logging

HASH_ALGORITHMS = {
    'md5': (hashlib.md5,128 * 64),
    'sha256': (hashlib.sha256, 256 * 64),
}

LOG = logging.getLogger('checksum')

def verify(data, digest, hashAlgo = 'md5'):
    '''Verify the integrity of a bytes-like object against a hash value'''

    assert( isinstance(digest,str) )

    try:
        h,hash_block_size = HASH_ALGORITHMS.get(hashAlgo)
    except KeyError:
        raise Exception('No support for the secure hashing algorithm')

    m = h()
    while True:
        d = data.read(hash_block_size)
        if not d:
            break
        m.update(d)

    res = m.hexdigest() == digest
    LOG.debug(' Calculated digest: ' + m.hexdigest())
    LOG.debug('Compared to digest: ' + digest)
    LOG.debug('\tMatching: ' + str(res))
    return res


