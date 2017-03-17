import json
import os
import shutil
from base64 import b64encode, b64decode

from .conf import CONF

def get_inbox(userId):
    return os.path.abspath( CONF.get('ingestion','inbox',raw=True) % { 'userId': userId } )

def get_data(data, datatype='bytes'):
    return json.loads(b64decode(data))

def create_staging_area(submission_id, group='org'):
    staging_area = os.path.abspath(
        os.path.join(
            CONF.get('ingestion','staging',raw=True) % {'submission' : submission_id },
            group
        )
    )
    os.makedirs(staging_area, exist_ok=True)
    return staging_area

def mv(filepath, target):
    shutil.copyfile( filepath, target )
    #os.rename( filepath, target )

def to_vault(filepath, submission_id, user_id):
    # vault_area = os.path.abspath(
    #     os.path.join(
    #         CONF.get('vault','location'),
    #         ''
    #     )
    # )
    # os.makedirs(vault_area, exist_ok=True)

    # os.rename( filepath, target )
    print('Not implemented yet')


def fake_data():
    return b64encode(b'{'
                     b'"submissionId":"12345",'
                     b'"user":"1002",'
                     b'"files":['
                     b'{  "filename":"test.gpg", '
                     b'   "encryptedHash": "efee20c02c7f51a53652c53cf703ef34", '
                     b'   "unencryptedHash" : "8e5cf4650dc93d88b23ca16ee8f08222", '
                     b'   "hashAlgorithm": "md5"'
                     b' },{'
                     b'   "filename":"test2", '
                     b'   "encryptedHash": "f6b86fe7ddcb72d0471b40663bd31c84e61f474a53b668b6915e81ca8062ff3c", '
                     b'   "unencryptedHash" : "ddaad93d5c412b05ecbff8683e9cae32871fb28d5a026dfcd3575b82cd80b320", '
                     b'   "hashAlgorithm": "sha256"'
                     b' },{'
                     b'   "filename":"test3", '
                     b'   "encryptedHash": "f6b86fe7ddcb72d0471b40663bd31c84e61f474a53b668b6915e81ca8062ff3c", '
                     b'   "unencryptedHash" : "ddaad93d5c412b05ecbff8683e9cae32871fb28d5a026dfcd3575b82cd80b320", '
                     b'   "hashAlgorithm": "sha256"'
                     b' }'
                     b']}')

def small_fake_data():
    return b64encode(b'{'
                     b'"submissionId":"738",'
                     b'"user":"1003",'
                     b'"files":['
                     b'{'
                     b'  "filename":"test-1.gpg", '
                     b'  "encryptedHash": "efee20c02c7f51a53652c53cf703ef34", '
                     b'  "unencryptedHash" : "8e5cf4650dc93d88b23ca16ee8f08222", '
                     b'  "hashAlgorithm": "md5"'
                     b'},{'
                     b'  "filename":"test-2.gpg", '
                     b'  "encryptedHash": "efee20c02c7f51a53652c53cf703ef34", '
                     b'  "unencryptedHash" : "8e5cf4650dc93d88b23ca16ee8f08222", '
                     b'  "hashAlgorithm": "md5"'
                     b'},{'
                     b'  "filename":"test-3.gpg", '
                     b'  "encryptedHash": "efee20c02c7f51a53652c53cf703ef34", '
                     b'  "unencryptedHash" : "8e5cf4650dc93d88b23ca16ee8f08222", '
                     b'  "hashAlgorithm": "md5"'
                     b'}'
                     b']}')
