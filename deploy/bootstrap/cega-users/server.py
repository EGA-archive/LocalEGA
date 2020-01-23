#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

'''
Test server to act as CentralEGA endpoint for users

:author: Frédéric Haziza
:copyright: (c) 2018, EGA System Developers.
'''

import sys
import os
import json
from base64 import b64decode
import ssl

from aiohttp import web

filepath = None
instances = {}
store = []
usernames = {}
uids = {}

# WSGI app
server = web.Application()

# SSL settings
ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile='/cega/CA.crt')
ssl_ctx.verify_mode = ssl.CERT_REQUIRED
ssl_ctx.check_hostname = False
ssl_ctx.load_cert_chain('/cega/ssl.crt', keyfile='/cega/ssl.key')

def fetch_user_info(identifier, query):
    id_type = query.get('idType', None)
    if not id_type:
        raise web.HTTPBadRequest(text='Missing or wrong idType')
    print(f'Requesting User {identifier} [type {id_type}]', file=sys.stderr)
    if id_type == 'username':
        pos = usernames.get(identifier, None)
        return store[pos] if pos is not None else None
    if id_type == 'uid':
        try:
            pos = uids.get(int(identifier), None)
            return store[pos] if pos is not None else None
        except Exception:
            return None
    raise web.HTTPBadRequest(text='Missing or wrong idType')

async def user(request):
    # Authenticate
    auth_header = request.headers.get('AUTHORIZATION')
    if not auth_header:
        raise web.HTTPUnauthorized(text=f'Protected access\n')
    _, token = auth_header.split(None, 1)  # Skipping the Basic keyword
    instance, passwd = b64decode(token).decode().split(':', 1)
    info = instances.get(instance)
    if info is None or info != passwd:
        raise web.HTTPUnauthorized(text=f'Protected access\n')

    # Find user
    user_info = fetch_user_info(request.match_info['identifier'], request.rel_url.query)
    if user_info is None:
        raise web.HTTPBadRequest(text=f'No info for that user\n')
    return web.json_response({ 'header': { "apiVersion": "v1",
                                           "code": "200",
                                           "service": "users",
                                           "developerMessage": "",
                                           "userMessage": "OK",
                                           "errorCode": "1",
                                           "docLink": "https://ega-archive.org",
                                           "errorStack": "" },
                               'response': { "numTotalResults": 1,
                                             "resultType": "eu.crg.ega.microservice.dto.lega.v1.users.LocalEgaUser",
                                             "result": [ user_info ]}
    })

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: {sys.argv[0] <hostaddr> <port> <filepath>}', file=sys.stderr)
        sys.exit(2)

    host = sys.argv[1]
    port = sys.argv[2]
    users_dir = sys.argv[3]

    # Init DB
    instances['legatest'] = 'legatest'  # Hard-coding legatest:legatest

    json_files = [os.path.join(users_dir, f)
                  for f in os.listdir(users_dir)
                  if os.path.isfile(os.path.join(users_dir, f)) and f.endswith('.json')]

    for i, user_file in enumerate(json_files):
        with open(user_file, 'rt') as f:
            d = json.load(f)
        store.append(d)
        usernames[d['username']] = i  # No KeyError, should be there
        uids[d['uid']] = i

    # Registering the routes
    server.router.add_get('/lega/v1/legas/users/{identifier}', user, name='user')
    # aaaand... cue music
    web.run_app(server, host=host, port=port, shutdown_timeout=0, ssl_context=ssl_ctx)
