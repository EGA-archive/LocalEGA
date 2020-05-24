#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import yaml

HOSTNAME_DOMAIN = os.getenv('HOSTNAME_DOMAIN','')

config = {
    'version': '3.7',

    'networks': {
        'external': None,
    },

    'services': {
        'cega-users': {
            'hostname': f'cega-users{HOSTNAME_DOMAIN}',
            # 'ports': ["15671:443"],
            'build': '../bootstrap/cega-users',
            'image': 'egarchive/cega-users:latest',
            'container_name': f'cega-users{HOSTNAME_DOMAIN}',
            'volumes': [
                './users:/cega/users',
                './certs/cega-users.cert.pem:/cega/ssl.crt',
                './certs/cega-users.sec.pem:/cega/ssl.key',
                './certs/CA.cega-users.cert.pem:/cega/CA.crt',
            ],
            'networks': ['external'],
        },

        'cega-mq': {
            'hostname': f'cega-mq{HOSTNAME_DOMAIN}',
            'ports': ["15670:15672", "5670:5671"],
            'image': 'rabbitmq:3.7.8-management-alpine',
            'container_name': f'cega-mq{HOSTNAME_DOMAIN}',
            'volumes': [
                './cega-mq-defs.json:/etc/rabbitmq/defs.json',
                './cega-mq-rabbitmq.config:/etc/rabbitmq/rabbitmq.config',
                './cega-entrypoint.sh:/usr/local/bin/cega-entrypoint.sh',
                './certs/cega-mq.cert.pem:/etc/rabbitmq/ssl.cert',
                './certs/cega-mq.sec.pem:/etc/rabbitmq/ssl.key',
                './certs/CA.cega-mq.cert.pem:/etc/rabbitmq/CA.cert',
            ],
            'networks': ['external'],
            'entrypoint': ["/usr/local/bin/cega-entrypoint.sh"],
        },

        'cega-accession': {
            'environment': [
                'LEGA_LOG=debug'
            ],
            'hostname': f'cega-accession{HOSTNAME_DOMAIN}',
            # 'ports': ["15671:443"],
            'image': 'egarchive/lega-base:latest',
            'container_name': f'cega-accession{HOSTNAME_DOMAIN}',
            'volumes': [
                './cega-accession.ini:/etc/ega/conf.ini:ro',
                '../bootstrap/cega-accession.py:/cega/accession.py',
                './certs/cega-accession.cert.pem:/cega/ssl.crt',
                './certs/cega-accession.sec.pem:/cega/ssl.key',
                './certs/CA.cega-accession.cert.pem:/cega/CA.crt',
            ],
            'networks': ['external'],
            'working_dir': '/cega',
            #'entrypoint': ["python", "accession.py"],
            'entrypoint': ["/bin/sleep", "100000000000"],
        },
    },
}

yaml.dump(config,
          sys.stdout,
          default_flow_style=False)
