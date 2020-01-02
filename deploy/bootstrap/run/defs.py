#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import secrets
import string
from base64 import b64encode
import hashlib
from importlib.util import find_spec

# check that bcrypt is installed for this python version
if find_spec("bcrypt") is None:
    print('The python bcrypt package is not found for this python version', file=sys.stderr)
    sys.exit(1)
else:
    import bcrypt

def generate_password(size):
    if os.getenv('DEPLOY_DEV'): # don't define it as an empty string, duh!
        return '-'*size
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(size))

def generate_bcrypt_hash(content):
    return bcrypt.hashpw(content.encode(), bcrypt.gensalt())

def generate_mq_hash(password):
    """Hashing password according to RabbitMQ specs."""
    # 1.Generate a random 32 bit salt:
    # This will generate 32 bits of random data:
    salt = os.urandom(4)

    # 2.Concatenate that with the UTF-8 representation of the password (in this case "simon")
    tmp0 = salt + password.encode('utf-8')

    # 3. Take the SHA256 hash and get the bytes back
    tmp1 = hashlib.sha256(tmp0).digest()

    # 4. Concatenate the salt again:
    salted_hash = salt + tmp1

    # 5. convert to base64 encoding:
    pass_hash = b64encode(salted_hash).decode("utf-8")

    return pass_hash

def get_or_die(var):
    val = os.getenv(var)
    if val is None:
        raise ValueError(f'{var} must be a defined env variable')
    return val

def get_file_content(filepath, mode='rb'):
    with open(filepath, mode=mode) as f:
        return f.read()
