#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import configparser

from docopt import docopt

__doc__ = f'''

Utility to help bootstrap a LocalEGA instance.

Usage:
   {sys.argv[0]} [options] <conf>

Options:
   -h, --help             Prints this help and exit
   -v, --version          Prints the version and exits
   -V, --verbose          Prints more output
   --archive_s3           With S3 as an archive backend
   --secrets <prefix>     Use this prefix for the docker secrets
 
'''

def main(conf, args):
    """Create verify.ini"""

    with_docker_secrets = args['--secrets']

    config = configparser.RawConfigParser()
    config['DEFAULT'] = {
        'queue': 'archived',
        'exchange': 'lega',
        'routing_key': 'completed',
        'master_key': 'c4gh_file',
    }

    master_key = ('secret:///run/secrets/master.key.passphrase'
                  if with_docker_secrets else
                  conf.get('master_key','passphrase', raw=True))

    config['c4gh_file'] = {
        'loader_class': 'C4GHFileKey',
        'passphrase': master_key,
        'filepath': '/etc/ega/ega.sec',
    }

    mq_connection = ('secret:///run/secrets/mq.connection'
                     if with_docker_secrets else
                     conf.get('mq', 'connection') + '?' + conf.get('mq', 'connection_params'))

    config['broker'] = {
        'connection': mq_connection,
        'enable_ssl': 'yes',
        'verify_peer': 'yes',
        'verify_hostname': 'no',
        'cacertfile': '/etc/ega/CA.cert',
        'certfile': '/etc/ega/ssl.cert',
        'keyfile': '/etc/ega/ssl.key',
    }

    db_connection = ('secret:///run/secrets/db.connection'
                     if with_docker_secrets else
                     conf.get('db', 'connection') + '?' + conf.get('db', 'connection_params'))

    config['db'] = {
        'connection': db_connection,
        'try': 30,
        'try_interval': 1,
    }

    if args['--archive_s3']:
        config['archive'] = {
            'storage_driver': 'S3Storage',
            's3_url': conf.get('s3', 'url'),
            's3_region': conf.get('s3', 'region'),
            's3_access_key': 'env://S3_ACCESS_KEY' , #conf.get('s3', 'access_key'),
            's3_secret_key': 'env://S3_SECRET_KEY' , #conf.get('s3', 'secret_key'),
            'cacertfile': '/etc/ega/CA.cert',
            'certfile': '/etc/ega/ssl.cert',
            'keyfile': '/etc/ega/ssl.key',
        }
    else:
        config['archive'] = {
            'storage_driver': 'FileStorage',
            'location': r'/ega/archive/%s/',
        }

    # output
    config.write(sys.stdout)


if __name__ == '__main__':
    args = docopt(__doc__,
                  sys.argv[1:],
                  help=True,
                  version='LocalEGA verify service boostrap (version 0.2)')
    conf = configparser.RawConfigParser()
    conf.read(args['<conf>'])
    main(conf, args)


