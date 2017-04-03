import json
import os
from pathlib import Path
import shutil
#import msgpack
from base64 import b64encode, b64decode

from .conf import CONF

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
    #shutil.copyfile( filepath, target )
    filepath.rename( target )

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
        {  "filename":"test.gpg",
           "encryptedIntegrity": {
               "hash": "efee20c02c7f51a53652c53cf703ef34",
               "algorithm": "md5"
           },
           "unencryptedIntegrity": {
               "hash": "8e5cf4650dc93d88b23ca16ee8f08222",
               "algorithm": "sha256"
           },
        },
        {
            "filename":"test2",
            "encryptedIntegrity": {
                "hash": "f6b86fe7ddcb72d0471b40663bd31c84e61f474a53b668b6915e81ca8062ff3c",
                "algorithm": "sha256"
            },
            "unencryptedIntegrity": {
                "hash": "ddaad93d5c412b05ecbff8683e9cae32871fb28d5a026dfcd3575b82cd80b320",
                "algorithm": "sha256"
            },
        },
        {
            "filename":"test3",
            "encryptedIntegrity": {
                "hash": "f6b86fe7ddcb72d0471b40663bd31c84e61f474a53b668b6915e81ca8062ff3c",
                "algorithm": "sha256"
            },
            "unencryptedIntegrity": {
                "hash": "ddaad93d5c412b05ecbff8683e9cae32871fb28d5a026dfcd3575b82cd80b320",
                "algorithm": "sha256"
            },
        }
    ],
}

f_data2 = {
    "submissionId": "738",
    "userId": "1003",
    "files":[
        {
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "8e41457344f195b29cfc4b37148385967c434ffeda958a47d3d7afbcc69323b6", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-bla.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-2.gpg",
            "encryptedIntegrity": { "hash": "8e41457344f195b29cfc4b37148385967c434ffeda958a47d3d7afbcc69323b6", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-4.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-5.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "md4" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha1" }
        },{
            "filename":"test-6.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-3.gpg",
            "encryptedIntegrity": { "hash": "8e41457344f195b29cfc4b37148385967c434ffeda958a47d3d7afbcc69323b6", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-7.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-8.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-9.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-a.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-b.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-c.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-d.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-e.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-f.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha1" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha1" }
        }
    ]
}

def fake_data():
    #return msgpack.packb(json.dumps(f_data).encode())
    return b64encode(json.dumps(f_data).encode())


def small_fake_data():
    #return msgpack.packb(json.dumps(f_data2).encode())
    return b64encode(json.dumps(f_data2).encode())
