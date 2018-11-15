'''Creating a rabbitmq hash of a supplied password'''

import sys
import os
from base64 import b64encode
import hashlib

# inspired by https://gist.github.com/komuw/c6fb1a1c757afb43fe69bdd736d5cf63
def hash_pass(password):
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


if __name__ == '__main__':

    if len(sys.argv) > 1:
        print(hash_pass(sys.argv[1]))
    else:
        password = input()
        print(hash_pass(password.strip()))
