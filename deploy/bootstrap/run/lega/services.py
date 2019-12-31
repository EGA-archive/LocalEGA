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

def main(cega_conf, conf, args):
    lega = {
        'version': '3.7',
        'networks': {
            'external': None,
            'internal': None,
            'private-db': None,
            'private-vault': None,
        },
        'volumes': { # Use the default driver for volume creation
            'mq': None,
            'db': None,
            'inbox': None,
            'archive': None,
        }
    }

    with_s3 = args['--archive_s3']
    if not with_s3:
        lega['volumes']['archive'] = None


    lega['services'] = {
        'mq': {
            'environment': [
                'CEGA_CONNECTION='+cega_conf.get('mq', 'connection'),
                'MQ_USER=admin',
                'MQ_PASSWORD_HASH='+conf.get('mq', 'password_hash'),
                'MQ_CA=/etc/rabbitmq/CA.cert',
                'MQ_SERVER_CERT=/etc/rabbitmq/ssl.cert',
                'MQ_SERVER_KEY=/etc/rabbitmq/ssl.key',
            ],
            'hostname': f'mq{HOSTNAME_DOMAIN}',
            'ports': [
                conf.get('docker-ports', 'mq')+':15672',
            ],
            'image': 'egarchive/lega-mq:latest',
            'container_name': f'mq{HOSTNAME_DOMAIN}',
            'networks': [
                'internal',
                'external',  # Only so that it is simpler to reach the cega-mq.
                             # Normally, we'd have routing to cega-mq
            ],
            'volumes': [
                'mq:/var/lib/rabbitmq',
                '../bootstrap/certs/data/mq.cert.pem:/etc/rabbitmq/ssl.cert',
                '../bootstrap/certs/data/mq.sec.pem:/etc/rabbitmq/ssl.key',
                '../bootstrap/certs/data/CA.mq.cert.pem:/etc/rabbitmq/CA.cert',
            ],
        },
        'db': {
            'environment': [
                'DB_LEGA_IN_PASSWORD='+conf.get('db', 'lega_in'),
                'DB_LEGA_OUT_PASSWORD='+conf.get('db', 'lega_out'),
                'PGDATA=/ega/data',
                'PG_SERVER_CERT=/etc/ega/pg.cert',
                'PG_SERVER_KEY=/etc/ega/pg.key',
                'PG_CA=/etc/ega/CA.cert',
                'PG_VERIFY_PEER=1',
            ],
            'hostname': f'db{HOSTNAME_DOMAIN}',
            'container_name': f'db{HOSTNAME_DOMAIN}',
            'image': 'egarchive/lega-db:latest',
            'volumes': [
                'db:/ega/data',
                '../bootstrap/certs/data/db.cert.pem:/etc/ega/pg.cert',
                '../bootstrap/certs/data/db.sec.pem:/etc/ega/pg.key',
                '../bootstrap/certs/data/CA.db.cert.pem:/etc/ega/CA.cert',
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
                'internal',
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
                '/home/daz/_local_inbox:/root/inbox', # debugging
                '../bootstrap/certs/data/inbox.cert.pem:/etc/ega/ssl.cert',
                '../bootstrap/certs/data/inbox.sec.pem:/etc/ega/ssl.key',
                '../bootstrap/certs/data/CA.inbox.cert.pem:/etc/ega/CA.cert',
            ],
            'entrypoint': ['/bin/sleep','10000000'], # debugging
        },

        'ingest': {
            'environment': [
                'LEGA_LOG=debug',
            ],
            'hostname': f'ingest{HOSTNAME_DOMAIN}',
            'image': 'egarchive/lega-base:latest',
            'container_name': f'ingest{HOSTNAME_DOMAIN}',
            'volumes': [
                # ../../../lega:/home/lega/.local/lib/python3.6/site-packages/lega',
                'inbox:/ega/inbox',
                './ingest.ini:/etc/ega/conf.ini:ro',
                './entrypoint.sh:/usr/local/bin/lega-entrypoint.sh',
                '../bootstrap/certs/data/ingest.cert.pem:/etc/ega/ssl.cert',
                '../bootstrap/certs/data/ingest.sec.pem:/etc/ega/ssl.key',
                '../bootstrap/certs/data/CA.ingest.cert.pem:/etc/ega/CA.cert',
            ] + ([] if with_s3 else ['archive:/ega/archive']),
            'networks': [
                'internal',
                'private-db',
                'private-vault',
            ],
            'user': 'lega',
            'entrypoint': ["lega-entrypoint.sh"],
            'command': ["ega-ingest"],
            # 'entrypoint': ["/bin/sleep", "1000000000000"]
        },

        'verify': {
            'environment': [
                'LEGA_LOG=debug',
            ] + ([
                'S3_ACCESS_KEY='+conf.get('s3','access_key'),
                'S3_SECRET_KEY='+conf.get('s3','secret_key'),
                'AWS_ACCESS_KEY_ID='+conf.get('s3','access_key'),
                'AWS_SECRET_ACCESS_KEY='+conf.get('s3','secret_key'),
            ] if with_s3 else []),
            'hostname': f'verify{HOSTNAME_DOMAIN}',
            'image': 'egarchive/lega-base:latest',
            'container_name': f'verify{HOSTNAME_DOMAIN}',
            'volumes': [
                # ../../../lega:/home/lega/.local/lib/python3.6/site-packages/lega',
                './verify.ini:/etc/ega/conf.ini:ro',
                './master.key.sec:/etc/ega/ega.sec',
                './entrypoint.sh:/usr/local/bin/lega-entrypoint.sh',
                '../bootstrap/certs/data/verify.cert.pem:/etc/ega/ssl.cert',
                '../bootstrap/certs/data/verify.sec.pem:/etc/ega/ssl.key',
                '../bootstrap/certs/data/CA.verify.cert.pem:/etc/ega/CA.cert',
            ] + ([] if with_s3 else ['archive:/ega/archive']),
            'networks': [
                'internal',
                'private-db',
                'private-vault',
            ],
            'user': 'lega',
            'entrypoint': ["lega-entrypoint.sh"],
            'command': ["ega-verify"],
            # 'entrypoint': ["/bin/sleep", "1000000000000"]
        },

        'finalize': {
            'environment': [
                'LEGA_LOG=debug'
            ],
            'hostname': f'finalize{HOSTNAME_DOMAIN}',
            'image': 'egarchive/lega-base:latest',
            'container_name': f'finalize{HOSTNAME_DOMAIN}',
            'volumes': [
                # ../../../lega:/home/lega/.local/lib/python3.6/site-packages/lega',
                './finalize.ini:/etc/ega/conf.ini:ro',
                './entrypoint.sh:/usr/local/bin/lega-entrypoint.sh',
                '../bootstrap/certs/data/finalize.cert.pem:/etc/ega/ssl.cert',
                '../bootstrap/certs/data/finalize.sec.pem:/etc/ega/ssl.key',
                '../bootstrap/certs/data/CA.finalize.cert.pem:/etc/ega/CA.cert',
            ],
            'networks': [
                'internal',
                'private-db',
            ],
            'user': 'lega',
            'entrypoint': ["lega-entrypoint.sh"],
            'command': ["ega-finalize"],
            # 'entrypoint': ["/bin/sleep", "1000000000000"]
        }
    }

    if with_s3:
        lega['services']['archive'] = {
            'hostname': f'archive{HOSTNAME_DOMAIN}',
            'container_name': f'archive{HOSTNAME_DOMAIN}',
            'image': 'minio/minio:RELEASE.2018-12-19T23-46-24Z',
            'environment': [
                'MINIO_ACCESS_KEY=',
                'MINIO_SECRET_KEY=',
            ],
            'volumes': [
                'archive:/data',
                '../bootstrap/certs/data/archive.cert.pem:/root/.minio/certs/public.crt',
                '../bootstrap/certs/data/archive.sec.pem:/root/.minio/certs/private.key',
                '../bootstrap/certs/data/CA.archive.cert.pem:/root/.minio/CAs/LocalEGA.crt',
            ],
            'networks': [
                'private-vault',
            ],
            # 'ports': [
            #     conf.get('docker-ports','s3')+":9000"
            # ],
            'command': ["server", "/data"]
        }

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
                  version='LocalEGA docker services boostrap (version 0.2)')

    conf = configparser.RawConfigParser()
    conf.read(args['<conf>'])

    cega_conf = configparser.RawConfigParser()
    cega_conf.read(args['<cega_conf>'])

    main(cega_conf, conf, args)




