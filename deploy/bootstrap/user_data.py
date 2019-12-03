import bcrypt
import argparse
import json

parser = argparse.ArgumentParser(description='encode data for url inclusion')

parser.add_argument('password', default="", help='password')
parser.add_argument('user', default="", help='user')
parser.add_argument('uid', default="", help='uid')
parser.add_argument('pubkey', default="", help='public key')
parser.add_argument('path', default="", help='public key')

args = parser.parse_args()

pass_hash = bcrypt.hashpw(args.password.encode('utf-8'), bcrypt.gensalt())


data = {"username": args.user,
        "uid": int(args.uid),
        "passwordHash": pass_hash.decode("utf-8"),
        "gecos": f"LocalEGA user {args.user}",
        "sshPublicKey": args.pubkey,
        "enabled": None}

with open(f'{args.path}/{args.user}.json', "w") as user_file:
    json.dump(data, user_file, ensure_ascii=False, indent=4)
