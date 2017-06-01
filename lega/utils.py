import json
#import logging
from pathlib import Path
import shutil
#import msgpack
from base64 import b64encode, b64decode
import functools

from aiohttp.web import HTTPUnauthorized

from .conf import CONF
from . import db

#LOG = logging.getLogger('utils')

def cache_var(v):
    '''Decorator to cache into a global variable'''
    def decorator(func):
        def wrapper(*args, **kwargs):
            g = globals()
            if v not in g:
                g[v] = func(*args, **kwargs)
            return g[v]
        return wrapper
    return decorator

def only_central_ega(async_func):
    '''Decorator restrain endpoint access to only Central EGA'''
    @functools.wraps(async_func)
    async def wrapper(request):
        # Just an example
        if request.headers.get('X-CentralEGA', 'no') != 'yes':
            raise HTTPUnauthorized(text='Not authorized. You should be Central EGA.\n')
        # Otherwise, it is from CentralEGA, we continue
        res = async_func(request)
        res.__name__ = getattr(async_func, '__name__', None)
        res.__qualname__ = getattr(async_func, '__qualname__', None)
        return (await res)
    return wrapper

def check_error(func):
    '''Decorator to store the raised exception in the database'''
    @functools.wraps(func)
    def wrapper(data):
        try:
            res = func(data)
            res.__name__ = getattr(func, '__name__', None)
            res.__qualname__ = getattr(func, '__qualname__', None)
            return res
        except Exception as e:
            if isinstance(e,AssertionError):
                raise e
            db.add_error(e)
    return wrapper

def get_inbox(userId):
    return 

def get_staging_area(seed, create=False):
    '''Build the staging area'''

def get_data(data):
    try:
        return json.loads(b64decode(data))
    except Exception as e:
        print(repr(e))
        return None
    #return json.loads(msgpack.unpackb(data))

def checksum(data, digest, hashAlgo = 'md5', block_size=8192):
    '''Verify the integrity of a bytes-like object against a hash value'''

    assert( isinstance(digest,str) )

    try:
        import hashlib
        from .crypto import HASH_ALGORITHMS
        h = HASH_ALGORITHMS.get(hashAlgo)
    except KeyError:
        raise Exception('No support for the secure hashing algorithm')

    m = h()
    while True:
        d = data.read(block_size)
        if not d:
            break
        m.update(d)

    res = m.hexdigest() == digest
    # LOG.debug(' Calculated digest: ' + m.hexdigest())
    # LOG.debug('Compared to digest: ' + digest)
    # LOG.debug('\tMatching: ' + str(res))
    return res
