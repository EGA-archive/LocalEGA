from base64 import b64encode
import os
import hashlib
import argparse


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


def main():
    """Make magic happen."""
    parser = argparse.ArgumentParser(description='''Creating public/private PGP keys''')

    parser.add_argument('password', help='PGP user name')
    args = parser.parse_args()

    password_hash = hash_pass(args.password)
    print(password_hash)


if __name__ == '__main__':
    main()
