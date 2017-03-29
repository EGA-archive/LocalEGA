import json
import os
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
    return os.path.abspath( CONF.get('ingestion','inbox',raw=True) % { 'userId': userId } )

def staging_area(submission_id, create=False, afterEncryption=False):
    '''Build the staging area'''
    group = '_enc' if afterEncryption else ''
    area = os.path.abspath( CONF.get('ingestion','staging',raw=True) % { 'submission': submission_id } + group)
    if create:
        shutil.rmtree(area, ignore_errors=True) # delete
        os.makedirs(area, exist_ok=True)        # re-create
    return area

async def mv(filepath, target):
    '''Moving (actually copying) the file to the another location'''
    shutil.copyfile( filepath, target )
    #os.rename( filepath, target )

async def to_vault(filepath, submission_id, user_id):
    '''Moving the file to the vault'''
    vault_area = os.path.abspath(
        os.path.join( CONF.get('vault','location'), submission_id )
    )
    os.makedirs(vault_area, exist_ok=True)

    filename = os.path.basename(filepath)
    # Moving the file
    os.rename( filepath,
               os.path.join(vault_area, filename)
    )

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
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "md4" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha1" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-3.gpg",
            "encryptedIntegrity": { "hash": "8e41457344f195b29cfc4b37148385967c434ffeda958a47d3d7afbcc69323b6", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
            "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },
            "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }
        },{
            "filename":"test-1.gpg",
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
