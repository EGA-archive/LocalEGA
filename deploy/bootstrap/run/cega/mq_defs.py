#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import configparser
import json

def add_queue(qname, vhost):
    return {
        "name": qname,
        "vhost": vhost,
        "durable":True,
        "auto_delete":False,
        "arguments": {}
    }

def add_binding(exchange, vhost, destination, key):
    return {
        "source": exchange,
        "vhost": vhost,
        "destination_type": "queue", 
        "arguments": {},
        "destination": destination, 
        "routing_key": key
    }

def main(confs):
    exchange = confs.get('mq', 'exchange')
    vhost = confs.get('mq', 'vhost')
    return {
        "rabbit_version": confs.get('mq', 'version'),
        "users":[
            { "name": confs.get('mq', 'user'),
              "password_hash": confs.get('mq', 'password_hash'),
              "hashing_algorithm":"rabbit_password_hashing_sha256",
              "tags":"administrator",
            }
        ],
        "vhosts":[
            {
                "name": vhost,
            }
        ],
        "permissions":[
            {
                "user": confs.get('mq', 'user'), 
                "vhost": vhost,
                "configure":".*",
                "write":".*",
                "read":".*"
            }
        ],
        "parameters": [],
        "global_parameters": [
            {
                "name":"cluster_name",
                "value":"rabbit@localhost"
            }
        ],
        "policies": [],
        "queues":[
            add_queue('v1.files', vhost),
            add_queue('v1.files.inbox', vhost),
            add_queue('v1.files.verified', vhost),
            add_queue('v1.files.completed', vhost),
            # add_queue('v1.files.processing', vhost),
            add_queue('v1.files.error', vhost),
        ],
        "exchanges": [
            {
                "name":"localega",
                "vhost": vhost,
                "type":"topic",
                "durable":True,
                "auto_delete":False,
                "internal":False,
                "arguments": {}
            }
        ],
        "bindings": [
            add_binding(exchange, vhost, 'v1.files', 'accession'),
            add_binding(exchange, vhost, 'v1.files', 'files'),
            add_binding(exchange, vhost, 'v1.files', 'mapping'),
            add_binding(exchange, vhost, 'v1.files.inbox', 'files.inbox'),
            add_binding(exchange, vhost, 'v1.files.error','files.error'),
            add_binding(exchange, vhost, 'v1.files.processing', 'files.processing'),
            add_binding(exchange, vhost, 'v1.files.completed', 'files.completed'),
            add_binding(exchange, vhost, 'v1.files.verified', 'files.verified'),
        ]
    }


if __name__ == '__main__':

    config = configparser.RawConfigParser()
    config.read_file(sys.stdin)
    res = json.dumps(main(config), indent=4)
    sys.stdout.write(res)
