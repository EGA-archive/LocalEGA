#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from urllib.parse import urlencode
import configparser

from ..defs import generate_mq_hash 

HOSTNAME_DOMAIN = os.getenv('HOSTNAME_DOMAIN','')

cega_connection_params=urlencode({ 'heartbeat': 0,
				   'connection_attempts': 30,
				   'retry_delay': 10,
				   'server_name_indication': f'cega-mq{HOSTNAME_DOMAIN}',
				   'verify': 'verify_peer',
				   'fail_if_no_peer_cert': 'true',
				   'cacertfile': '/etc/rabbitmq/CA.cert',
				   'certfile': '/etc/rabbitmq/ssl.cert',
				   'keyfile': '/etc/rabbitmq/ssl.key',
}, safe='/-_.')

config = configparser.RawConfigParser()

config['DEFAULT'] = {}
config['mq'] = {
    'version': '3.7.8',
    'connection': f"amqps://legatest:legatest@cega-mq{HOSTNAME_DOMAIN}:5671/lega",
    'connection_params': cega_connection_params,
    'user': 'legatest',
    'password_hash': generate_mq_hash('legatest'),
    'vhost': 'lega',
    'exchange': 'localega.v1',
}
config['users'] = {
    'endpoint': r'https://cega-users/lega/v1/legas/users',
    'credentials': 'legatest:legatest',
}

# output
config.write(sys.stdout)
