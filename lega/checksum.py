import hashlib

## Supported secure hash
HASH_ALGORITHMS = {
    'md5': (hashlib.md5,128 * 64),
    'sha256': (hashlib.sha256, 256 * 64),
}


def verify(data, digest, hashAlgo = 'md5'):
    '''Verify the integrity of a bytes-like object against a hash value'''

    assert( isinstance(digest,str) )

    try:
        h,hash_block_size = HASH_ALGORITHMS.get(hashAlgo)
    except KeyError:
        raise Exception('No support for the secure hashing algorithm')

    m = h()
    #m.update(f.read())
    while True:
        d = data.read(hash_block_size)
        if not d:
            break
        m.update(d)

    return m.hexdigest() == digest
