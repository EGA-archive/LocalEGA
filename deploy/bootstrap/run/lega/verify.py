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
    config = configparser.RawConfigParser()
    config['DEFAULT'] = {
        'log':'debug',
        'master_key': 'c4gh_file',
    }
    config['c4gh_file'] = {
        'loader_class': 'C4GHFileKey',
        'passphrase': conf.get('master_key','passphrase', raw=True),
        'filepath': '/etc/ega/ega.sec',
    }
    config['inbox'] = {
        'location': r'/ega/inbox/%s/',
        'chroot_sessions': True,
    }
    config['broker'] = {
        'connection': conf.get('mq', 'connection') + '?' + conf.get('mq', 'connection_params'),
        'enable_ssl': 'yes',
        'verify_peer': 'yes',
        'verify_hostname': 'no',
        'cacertfile': '/etc/ega/CA.cert',
        'certfile': '/etc/ega/ssl.cert',
        'keyfile': '/etc/ega/ssl.key',
    }
    config['db'] = {
        'connection': conf.get('db', 'connection') + '?' + conf.get('db', 'connection_params'),
        'try': 30,
        'try_interval': 1,
    }

    if args['--archive_s3']:
        config['archive'] = {
            'storage_driver': 'S3Storage',
            's3_url': conf.get('s3', 'url'),
            's3_access_key': conf.get('s3', 'access_key'),
            's3_secret_key': conf.get('s3', 'secret_key'),
            # 'region': 'lega',
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


