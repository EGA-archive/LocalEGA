import json
import os
import shutil
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

def get_data(data, datatype='bytes'):
    return json.loads(b64decode(data))

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

def mv(filepath, target):
    '''Moving (actually copying) the file to the another location'''
    shutil.copyfile( filepath, target )
    #os.rename( filepath, target )

def to_vault(filepath, submission_id, user_id):
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


def fake_data():
    return b64encode(b'{'
                     b'"submissionId":"12345",'
                     b'"userId":"1002",'
                     b'"files":['
                     b'{  "filename":"test.gpg", '
                     b'   "encryptedIntegrity": { "hash": "efee20c02c7f51a53652c53cf703ef34", "algorithm": "md5" },'
                     b'   "unencryptedIntegrity": { "hash": "8e5cf4650dc93d88b23ca16ee8f08222", "algorithm": "sha256" }'
                     b' },{'
                     b'   "filename":"test2", '
                     b'   "encryptedIntegrity": { "hash": "f6b86fe7ddcb72d0471b40663bd31c84e61f474a53b668b6915e81ca8062ff3c", "algorithm": "sha256" },'
                     b'   "unencryptedIntegrity": { "hash": "ddaad93d5c412b05ecbff8683e9cae32871fb28d5a026dfcd3575b82cd80b320", "algorithm": "sha256" }'
                     b' },{'
                     b'   "filename":"test3", '
                     b'   "encryptedIntegrity": { "hash": "f6b86fe7ddcb72d0471b40663bd31c84e61f474a53b668b6915e81ca8062ff3c", "algorithm": "sha256" },'
                     b'   "unencryptedIntegrity": { "hash": "ddaad93d5c412b05ecbff8683e9cae32871fb28d5a026dfcd3575b82cd80b320", "algorithm": "sha256" }'
                     b' }'
                     b']}')

def small_fake_data():
    return b64encode(b'{'
                     b'"submissionId":"738",'
                     b'"userId":"1003",'
                     b'"files":['
                     b'{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "8e41457344f195b29cfc4b37148385967c434ffeda958a47d3d7afbcc69323b6", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-bla.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-2.gpg", '
                     b'  "encryptedIntegrity": { "hash": "8e41457344f195b29cfc4b37148385967c434ffeda958a47d3d7afbcc69323b6", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "md4" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha1" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-3.gpg", '
                     b'  "encryptedIntegrity": { "hash": "8e41457344f195b29cfc4b37148385967c434ffeda958a47d3d7afbcc69323b6", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha256" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha256" }'
                     b'},{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedIntegrity": { "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "algorithm": "sha1" },'
                     b'  "unencryptedIntegrity": { "hash": "29da20d8dc8ab1a8830c0ea0c4d7e41a84d82cf040ae4c7932145bd5fd7cded3", "algorithm": "sha1" }'
                     b'}'
                     b']}')
