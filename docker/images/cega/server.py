#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

'''
Test server to act as CentralEGA endpoint for users

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import os
import asyncio
import yaml
from pathlib import Path
from functools import wraps
from base64 import b64decode
import logging
from aiohttp import web
import jinja2
import aiohttp_jinja2


FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

instances = {}
for instance in os.environ.get('LEGA_INSTANCES', '').strip().split(','):
    instances[instance] = (Path(f'/cega/users/{instance}'), os.environ[f'CEGA_REST_{instance}_PASSWORD'])

fixed_header = {"apiVersion": "v1",
                "code": "200",
                "service": "users",
                "developerMessage": "",
                "userMessage": "OK",
                "errorCode": "1",
                "docLink": "https://ega-archive.org",
                "errorStack": ""}


def protected(func):
    @wraps(func)
    def wrapped(request):
        auth_header = request.headers.get('AUTHORIZATION')
        if not auth_header:
            raise web.HTTPUnauthorized(text=f'Protected access\n')
        _, token = auth_header.split(None, 1)  # Skipping the Basic keyword
        instance, passwd = b64decode(token).decode().split(':', 1)
        info = instances.get(instance)
        if info is not None and info[1] == passwd:
            request.match_info['lega'] = instance
            request.match_info['users_dir'] = info[0]
            return func(request)
        raise web.HTTPUnauthorized(text=f'Protected access\n')
    return wrapped


@aiohttp_jinja2.template('users.html')
async def index(request):
    users = {}
    for instance, (users_dir, _) in instances.items():
        users[instance] = {}
        files = (f for f in users_dir.iterdir() if f.is_file())
        for f in files:
            with open(f, 'r') as stream:
                users[instance][f.stem] = yaml.load(stream)
    return {"cega_users": users}


@protected
async def user(request):
    lega_instance = request.match_info['lega']
    users_dir = request.match_info['users_dir']
    identifier = request.match_info['identifier']

    if 'idType' in request.rel_url.query and request.rel_url.query['idType'] == 'username':
        id_type = request.rel_url.query['idType']
        LOG.info(f'User ID request: {lega_instance}, in {users_dir}, with request of id type {id_type} and name {identifier}.')
        try:
            with open(f'{users_dir}/{identifier}.yml', 'r') as stream:
                data = dict()
                data['header'] = fixed_header
                d = yaml.load(stream)
                # We are mocking this so we only need the result to be right
                data['response'] = {"numTotalResults": 1,
                                    "resultType": "eu.crg.ega.microservice.dto.lega.v1.users.LocalEgaUser",
                                    "result": [{'username': d.get("username", None),
                                                'passwordHash': d.get("password_hash", None),
                                                'sshPublicKey': d.get("pubkey", None),
                                                'uid': int(d.get("uid", None)),
                                                'gecos': d.get("gecos", "EGA User"),
                                                "enabled": None}]}
                return web.json_response(data)
        except OSError:
            raise web.HTTPBadRequest(text=f'No info for user {identifier} in LocalEGA {lega_instance}... yet\n')
    elif 'idType' in request.rel_url.query and request.rel_url.query['idType'] == 'uid':
        id_type = request.rel_url.query['idType']
        LOG.info(f'User ID request: {lega_instance}, in {users_dir}, with request of id type {id_type} and UID {identifier}.')
        try:
            with open(f'{users_dir}_ids/{identifier}.yml', 'r') as stream:
                data = dict()
                data['header'] = fixed_header
                d = yaml.load(stream)
                # We are mocking this so we only need the result to be right
                data['response'] = {"numTotalResults": 1,
                                    "resultType": "eu.crg.ega.microservice.dto.lega.v1.users.LocalEgaUser",
                                    "result": [{'username': d.get("username", None),
                                                'passwordHash': d.get("password_hash", None),
                                                'sshPublicKey': d.get("pubkey", None),
                                                'uid': int(d.get("uid", None)),
                                                'gecos': d.get("gecos", "EGA User"),
                                                "enabled": None}]}
                return web.json_response(data)
        except OSError:
            raise web.HTTPBadRequest(text=f'No info for user id {identifier} in LocalEGA {lega_instance}... yet\n')
    else:
        raise web.HTTPBadRequest(text='Missing or wrong idType')


# Unprotected access
async def pgp_pbk(request):
    name = request.match_info['id']
    try:
        with open(f'/ega/users/pgp/{name}.pub', 'r') as stream:  # 'rb'
            return web.Response(text=stream.read())              # .hex()
    except OSError:
        raise web.HTTPBadRequest(text=f'No info about {name} in CentralEGA... yet\n')


def main():

    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"

    sslcontext = None

    loop = asyncio.get_event_loop()
    server = web.Application(loop=loop)

    template_loader = jinja2.FileSystemLoader("/cega")
    aiohttp_jinja2.setup(server, loader=template_loader)

    # Registering the routes
    server.router.add_get('/', index, name='root')
    server.router.add_get('/lega/v1/legas/users/{identifier}', user, name='user')
    server.router.add_get('/pgp/{id}', pgp_pbk, name='pgp')

    web.run_app(server, host=host, port=80, shutdown_timeout=0, ssl_context=sslcontext)


if __name__ == '__main__':
    main()
