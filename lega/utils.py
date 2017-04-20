import json
import os
#import logging
from pathlib import Path
import shutil
#import msgpack
from base64 import b64encode, b64decode
import functools

from aiohttp.web import HTTPUnauthorized

from .conf import CONF

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

def get_inbox(userId):
    return Path( CONF.get('ingestion','inbox',raw=True) % { 'userId': userId } )

def staging_area(submission_id, create=False, afterEncryption=False):
    '''Build the staging area'''
    group = '_enc' if afterEncryption else ''
    area = Path( CONF.get('ingestion','staging',raw=True) % { 'submission': submission_id } + group)
    if create:
        shutil.rmtree(area, ignore_errors=True) # delete
        area.mkdir(parents=True, exist_ok=True) # re-create
    return area

def mv(filepath, target):
    '''Moving the file to the another location'''
    shutil.copyfile( str(filepath), str(target) )
    #filepath.rename( target )

def to_vault(filepath, submission_id, user_id):
    '''Moving the file to the vault'''
    vault_area = Path( CONF.get('vault','location')) / submission_id
    vault_area.mkdir(parents=True, exist_ok=True) # re-create

    filepath = Path(filepath) # In case it's a str
    target = vault_area / filepath.parts[-1]
    filepath.rename(target)

def get_data(data):
    return json.loads(b64decode(data))
    #return json.loads(msgpack.unpackb(data))

f_data = {
    "submissionId": "12345",
    "userId": "1002",
    "files": [
        {  "filename":"test2",
           "encryptedIntegrity": { "hash": "4c69a65417205d4766afbc18e38a5abd", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "5f8159fcc117ea2cae98ce6e1c1a6261", "algorithm": "md5" },
        },
        {  "filename":"test1",
           "encryptedIntegrity": { "hash": "ef46a1eff5fcc521e0fb5f2da8a78ab8", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" },
        },
        {  "filename":"test3",
           "encryptedIntegrity": { "hash": "d8bd5bf0178691b1dcd8f2a2e212fb188ac4f89c36d3a744b2e2ec157c426eac", "algorithm": "sha256" },
           "unencryptedIntegrity": { "hash": "ddaad93d5c412b05ecbff8683e9cae32871fb28d5a026dfcd3575b82cd80b320", "algorithm": "sha256" },
        },
    ],
}

f_data2 = {
    "submissionId": "738",
    "userId": "1003",
    "files":[
        {  "filename":"test-1",
           "encryptedIntegrity": { "hash": "ef46a1eff5fcc521e0fb5f2da8a78ab8", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" },
        },
        {  "filename":"test-2",
           "encryptedIntegrity": { "hash": "ef46a1eff5fcc521e0fb5f2da8a78ab8", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
        },
        {  "filename":"test-3",
           "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
        },
        {  "filename":"test-4",
           "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
        },
        {  "filename":"test-5",
           "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
        },
        {  "filename":"test-6",
           "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
        },
        {  "filename":"test-7",
           "encryptedIntegrity": { "hash": "0bd39dd908ecee4a97f0c25c1e8e272b6456fa48b09521982008f03b2403bcd", "algorithm": "sha256" },
           "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" },
        },
        {  "filename":"test-8",
           "encryptedIntegrity": { "hash": "ef46a1eff5fcc521e0fb5f2da8a78ab8", "algorithm": "md5" },
           "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" },
        },
        {  "filename":"test-9",
           "encryptedIntegrity": { "hash": "0bd39dd908ecee4a97f0c25c1e8e272b6456fa48b09521982008f03b2403bcd6", "algorithm": "sha256" },
           "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" },
        },
    ],
}

def fake_data():
    #return msgpack.packb(json.dumps(f_data).encode())
    return b64encode(json.dumps(f_data).encode())


def small_fake_data():
    #return msgpack.packb(json.dumps(f_data2).encode())
    return b64encode(json.dumps(f_data2).encode())
