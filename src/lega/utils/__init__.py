import json
import logging
from pathlib import Path
from base64 import b64encode, b64decode
from functools import wraps
import secrets
import string

from aiohttp.web import HTTPUnauthorized

from ..conf import CONF
from . import db
from .hash_algo import DIGEST as HASH_ALGORITHMS
from . import exceptions

LOG = logging.getLogger('utils')

def only_central_ega(async_func):
    '''Decorator restrain endpoint access to only Central EGA'''
    @wraps(async_func)
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

def db_log_error_on_files(func):
    '''Decorator to store the raised exception in the database'''
    @wraps(func)
    def wrapper(data):
        file_id = data['file_id'] # I should have it
        try:
            res = func(data)
            return res
        except Exception as e:
            if isinstance(e,AssertionError):
                raise e
            db.set_error(file_id, e)
    return wrapper

def catch_user_error(func):
    '''Decorator to store the raised exception in the database'''
    @wraps(func)
    def wrapper(data):
        user_id = data['user_id'] # I should have it
        try:
            res = func(data)
            return res
        except Exception as e:
            if isinstance(e,AssertionError):
                raise e
            db.set_user_error(user_id, e)
    return wrapper

def get_data(data):
    try:
        return json.loads(b64decode(data))
    except Exception as e:
        print(repr(e))
        return None
    #return json.loads(msgpack.unpackb(data))

def raw_checksum(f, d, h, bsize=8192):
    '''Computes the checksum of the bytes-like `f` using the algorithm `h`, and compares it to `d`.'''
    m = h()
    while True:
        data = f.read(bsize)
        if not data:
            break
        m.update(data)
    res = (m.hexdigest() == d)
    LOG.debug('Calculated digest: '+m.hexdigest())
    LOG.debug('  Original digest: '+d)
    return res

def checksum(filepath, digest, hashAlgo = 'md5', block_size=8192):
    '''Verify the integrity of a file against a hash value'''

    assert( isinstance(digest,str) )

    try:
        h = HASH_ALGORITHMS.get(hashAlgo)
    except KeyError:
        raise exceptions.UnsupportedHashAlgorithm(hashAlgo)

    with open(filepath, 'rb') as f: # Open the file in binary mode. No encoding dance.
        return raw_checksum(f, digest, h, bsize=block_size)


def get_checksum_from_companion(filepath):
    '''Attempts to read a companion file.

    For each digest algorithms (see utils/hash_algo.py),
    we check if a companion file exists.
    If so, we read its content and return it, along with the selected current algorithm.

    We exit at the first one found and raise a CompanionNotFound exception in case none worked.
    '''
    for h in HASH_ALGORITHMS:
        companion = str(filepath) + '.' + h
        try:
            with open(companion, 'rt', encoding='utf-8') as f:
                return f.read(), h
        except OSError as e: # Not found, not readable, ...
            LOG.debug(f'Companion {companion}: {e!r}')
            # Check the next

    else: # no break statement was encountered
        raise exceptions.CompanionNotFound(filepath)
        

alphabet = string.ascii_letters + string.digits
def generate_password(length):
    return ''.join(secrets.choice(alphabet) for i in range(length))

