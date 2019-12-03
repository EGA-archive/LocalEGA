import secrets
import string
import argparse

parser = argparse.ArgumentParser(description='encode data for url inclusion')

parser.add_argument('size', default="", help='size of password')

args = parser.parse_args()

print(''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(int(args.size))))
