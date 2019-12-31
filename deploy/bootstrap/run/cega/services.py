#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import yaml

HOSTNAME_DOMAIN = os.getenv('HOSTNAME_DOMAIN','')

config = {
    'version': '3.7',

    'services': {
        'cega-users': {
            'hostname': f'cega-users{HOSTNAME_DOMAIN}',
            'ports': ["15671:443"],
            'image': 'egarchive/lega-base:latest',
            'container_name': f'cega-users{HOSTNAME_DOMAIN}',
            'volumes': [
                '../cega-users.py:/cega/users.py',
                './users:/cega/users',
                '../certs/data/cega-users.cert.pem:/cega/ssl.crt',
                '../certs/data/cega-users.sec.pem:/cega/ssl.key',
                '../certs/data/CA.cega-users.cert.pem:/cega/CA.crt',
            ],
            'networks': ['external'],
            'user': 'root',
            'entrypoint': ["python", "/cega/users.py", "0.0.0.0", "443", "/cega/users"],
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
                '../certs/data/cega-mq.cert.pem:/etc/rabbitmq/ssl.cert',
                '../certs/data/cega-mq.sec.pem:/etc/rabbitmq/ssl.key',
                '../certs/data/CA.cega-mq.cert.pem:/etc/rabbitmq/CA.cert',
            ],
            'networks': ['external'],
            'entrypoint': ["/usr/local/bin/cega-entrypoint.sh"],
        },
    },
}

yaml.dump(config,
          sys.stdout,
          default_flow_style=False)
