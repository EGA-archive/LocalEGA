#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
from pathlib import Path
import json

from docopt import docopt

from ..defs import generate_password, get_file_content, generate_bcrypt_hash

__version__ = 0.2
__title__ = 'Generate CentralEGA fake users'

__doc__ = f'''

Utility to help generate users at fake CentralEGA for usage in a LocalEGA instance.

Usage:
   {sys.argv[0]} [options] <users_dir> <users_record>

Options:
   -h, --help        Prints this help and exit
   -v, --version     Prints the version and exits
 
'''

def main(users_dir, record, users):

    for name, user_id in users.items():

        passphrase = generate_password(8)

        filepath = users_dir / name
        if filepath.exists():
            os.remove(filepath)

        cmd = f'ssh-keygen -t ed25519 -f {filepath} -N "{passphrase}" -C "{name}@LocalEGA"'
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	
        # Bcrypt hash
        passphrase_hash=generate_bcrypt_hash(passphrase)

        with open(filepath.with_suffix('.json'), 'w') as f:
            json.dump({
	        "username" : name,
	        "uid" : user_id,
	        "passwordHash" : passphrase_hash.decode(),
                "gecos" : f"LocalEGA user {name}",
  	        "sshPublicKey" : get_file_content(filepath.with_suffix('.pub'), mode='rt'),
	        "enabled" : None
            },f)

        record.write(f"{name}:{filepath!s}:{passphrase}\n")



if __name__ == '__main__':
    args = docopt(__doc__, sys.argv[1:], help=True, version=f'{__title__} (version {__version__})')

    users_dir = Path(args['<users_dir>'])
    if not users_dir.exists():
        os.mkdir(users_dir)

    with open(args['<users_record>'], 'wt') as record:
        main(users_dir, record, {
            'dummy':15001,
            'john':15002,
            'jane':15003,
        })

