#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import configparser
from ruamel.yaml import YAML

from docopt import docopt

HOSTNAME_DOMAIN=os.getenv('HOSTNAME_DOMAIN','')

__doc__ = f'''

Utility to help bootstrap a LocalEGA instance.

Usage:
   {sys.argv[0]} [options] <cega_conf> <conf>

Options:
   -h, --help             Prints this help and exit
   -v, --version          Prints the version and exits
   -V, --verbose          Prints more output
   --archive_s3           With S3 as an archive backend
   --secrets <prefix>     Use this prefix for the docker secrets
 
'''

LEGA_LOG='LEGA_LOG=debug'
# LEGA_LOG='INGESTION_LOG=centralized'

def main(cega_conf, conf, args):
    lega = {
        'version': '3.7',
        'networks': {
            'external': None,
            'internal': None,
            'private-db': None,
        },
        'volumes': { # Use the default driver for volume creation
            'archive-db': None,
            'inbox': None,
            'archive': None,
        }
    }


    with_docker_secrets = args['--secrets']

    with_s3 = args['--archive_s3']
    if not with_s3:
        lega['volumes']['archive'] = None

    lega['services'] = {
        'archive-db': {
            'build': '../../ingestion/db',
            'environment': [
                'DB_PASSWORD='+conf.get('archive-db', 'password'),
                'PGDATA=/ega/data',
                'PG_SERVER_CERT=/etc/ega/pg.cert',
                'PG_SERVER_KEY=/etc/ega/pg.key',
                'PG_CA=/etc/ega/CA.cert',
                'PG_VERIFY_PEER=1',
            ],
            'hostname': f'archive-db{HOSTNAME_DOMAIN}',
            'container_name': f'archive-db{HOSTNAME_DOMAIN}',
            'image': 'egarchive/lega-db:latest',
            'volumes': [
                'archive-db:/ega/data',
                '../../ingestion/db/archive-db.sql:/etc/ega/db.sql', # booting 
                './certs/archive-db.cert.pem:/etc/ega/pg.cert',
                './certs/archive-db.sec.pem:/etc/ega/pg.key',
                './certs/CA.archive-db.cert.pem:/etc/ega/CA.cert',
            ],
            'networks': [
                'private-db',
            ],
        },
        'inbox': {
            'hostname': f'inbox{HOSTNAME_DOMAIN}',
            'depends_on': [
                'mq',     # Required external link
            ],
            'container_name': f'inbox{HOSTNAME_DOMAIN}',
            'networks': [
                'external',
                'internal', # to reach local MQ
            ],
            'environment': [
                'CEGA_ENDPOINT='+cega_conf.get('users', 'endpoint'),
                'CEGA_ENDPOINT_CREDS='+cega_conf.get('users', 'credentials'),
                'CEGA_ENDPOINT_JSON_PREFIX=response.result',
                'MQ_CONNECTION='+conf.get('mq','connection'), # without the connection_params
                'MQ_EXCHANGE='+conf.get('mq','mq_exchange'),
                'MQ_ROUTING_KEY='+conf.get('mq','mq_routing_key'),
                'MQ_VERIFY_PEER=yes',
                'MQ_VERIFY_HOSTNAME=no',
                'MQ_CA=/etc/ega/CA.cert',
                'MQ_CLIENT_CERT=/etc/ega/ssl.cert',
                'MQ_CLIENT_KEY=/etc/ega/ssl.key',
                'AUTH_VERIFY_PEER=yes',
                'AUTH_VERIFY_HOSTNAME=yes',
                'AUTH_CA=/etc/ega/CA.cert',
                'AUTH_CLIENT_CERT=/etc/ega/ssl.cert',
                'AUTH_CLIENT_KEY=/etc/ega/ssl.key',
            ],
            'ports': [
                conf.get('docker-ports','inbox')+":9000"
            ],
            'image': 'egarchive/lega-inbox:latest',
            'volumes': [
                'inbox:/ega/inbox',
                './certs/inbox.cert.pem:/etc/ega/ssl.cert',
                './certs/inbox.sec.pem:/etc/ega/ssl.key',
                './certs/CA.inbox.cert.pem:/etc/ega/CA.cert',
            ],
        },
    }


    if with_s3:
        lega['networks']['private-vault'] = None
        lega['services']['archive'] = {
            'hostname': f'archive{HOSTNAME_DOMAIN}',
            'container_name': f'archive{HOSTNAME_DOMAIN}',
            'image': 'minio/minio:RELEASE.2018-12-19T23-46-24Z',
            'environment': [
                'MINIO_ACCESS_KEY='+conf.get('s3','access_key'),
                'MINIO_SECRET_KEY='+conf.get('s3','secret_key'),
            ],
            'volumes': [
                'archive:/data',
                './certs/archive.cert.pem:/root/.minio/certs/public.crt',
                './certs/archive.sec.pem:/root/.minio/certs/private.key',
                './certs/CA.archive.cert.pem:/root/.minio/CAs/LocalEGA.crt',
            ],
            'networks': [
                'private-vault',
            ],
            # 'ports': [
            #     conf.get('docker-ports','s3')+":9000"
            # ],
            'command': ["server", "/data"]
        }

    if with_docker_secrets:
        lega['secrets'] = {
            'archive-db.connection': { 'file': './secrets/archive-db.connection'         },
        }

        # create the files 
        from ..defs import put_file_content
        db_connection = conf.get('archive-db', 'connection') + '?' + conf.get('archive-db', 'connection_params')
        put_file_content(args['--secrets'], 'archive-db.connection', db_connection.encode())

    yaml=YAML()
    yaml.default_flow_style = False
    yaml.dump(lega, sys.stdout)

    # yaml.dump(lega,
    #           sys.stdout,
    #           default_flow_style=False)


if __name__ == '__main__':
    args = docopt(__doc__,
                  sys.argv[1:],
                  help=True,
                  version='LocalEGA stub services boostrap (version 0.2)')

    conf = configparser.RawConfigParser()
    conf.read(args['<conf>'])

    cega_conf = configparser.RawConfigParser()
    cega_conf.read(args['<cega_conf>'])

    main(cega_conf, conf, args)




