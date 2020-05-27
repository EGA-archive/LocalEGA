#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import configparser
from urllib.parse import urlencode

from docopt import docopt

from ..defs import generate_password, generate_mq_hash, get_file_content

__version__ = 0.2
__title__ = 'LocalEGA bootstrap password generator script'

HOSTNAME_DOMAIN = os.getenv('HOSTNAME_DOMAIN', '')

__doc__ = f'''

Utility to help generate random passwords for bootstrapping a LocalEGA instance.

Usage:
   {sys.argv[0]} [options]

Options:
   -h, --help             Prints this help and exit
   -v, --version          Prints the version and exits
   --secrets <dir>        Secrets directory [Default: private/secrets]
 
'''

def main(args):

    def get_secret(s):
        return get_file_content(os.path.join(args['--secrets'], s), mode='rt')

    config = configparser.RawConfigParser()

    config['DEFAULT'] = { 'log': 'DEBUG' }

    config['docker-ports'] = {
        'inbox':2222,
        'mq': 15672,
        'archive-db': 15432,
    }


    #################################################
    #### Local Message Broker
    #################################################
    mq_user = 'admin'
    mq_password = get_secret('mq.admin')

    # Pika is not parsing the URL the way RabbitMQ likes.
    # So we add the parameters on the configuration file and
    # create the SSL socket ourselves
    # Some parameters can be passed in the URL, though.
    mq_connection=f"amqps://{mq_user}:{mq_password}@mq{HOSTNAME_DOMAIN}:5671/%2F"
    mq_connection_params = urlencode({ 'heartbeat': 0,
				       'connection_attempts': 30,
				       'retry_delay': 10 })

    mq_exchange = 'cega'
    mq_routing_key = 'files.inbox'

    config['mq'] = {
        'user': mq_user,
        'password': mq_password,
        'password_hash': generate_mq_hash(mq_password),
        'connection': mq_connection,
        'connection_params': mq_connection_params,
        'mq_exchange': mq_exchange,
        'mq_routing_key': mq_routing_key,
    }

    #################################################
    #### Local Database
    #################################################

    db_lega_pwd = get_secret('db.lega')
    db_connection_params = urlencode({ 'application_name': 'LocalEGA',
				       'sslmode': 'verify-full',
				       'sslcert': '/etc/ega/ssl.cert',
				       'sslkey': '/etc/ega/ssl.key.lega',
				       'sslrootcert': '/etc/ega/CA.cert',
    }, safe='/-_.')
    db_connection=f"postgres://lega:{db_lega_pwd}@db{HOSTNAME_DOMAIN}:5432/lega"

    config['db'] = {
        'user': 'lega',
        'password': db_lega_pwd,
        'connection': db_connection,
        'connection_params': db_connection_params,
    }

    #################################################
    #### Storage Database
    #################################################

    archive_db_lega_pwd = get_secret('archive-db.lega')
    archive_db_connection_params = urlencode({ 'application_name': 'LocalEGA',
				               'sslmode': 'verify-full',
				               'sslcert': '/etc/ega/ssl.cert',
				               'sslkey': '/etc/ega/ssl.key.lega',
				               'sslrootcert': '/etc/ega/CA.cert',
    }, safe='/-_.')
    archive_db_connection=f"postgres://lega:{archive_db_lega_pwd}@archive-db{HOSTNAME_DOMAIN}:5432/lega"

    config['archive-db'] = {
        'user': 'lega',
        'password': archive_db_lega_pwd,
        'connection': archive_db_connection,
        'connection_params': archive_db_connection_params,
    }


    #################################################
    #### Master key
    #################################################

    config['master_key'] = {
        'passphrase': get_secret('master.key.passphrase')
    }

    return config


if __name__ == '__main__':
    version = f'{__title__} (version {__version__})'
    args = docopt(__doc__, sys.argv[1:], help=True, version=version)
    main(args).write(sys.stdout)
