#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

'''
Test server to act as CentralEGA endpoint for users

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import asyncio
import ssl
import yaml
from pathlib import Path

from aiohttp import web
import jinja2
import aiohttp_jinja2

# For the match, we turn that off
ssl.match_hostname = lambda cert, hostname: True

@aiohttp_jinja2.template('users.html')
async def index(request):
    users_dir = Path('/cega/users')
    files = [f for f in users_dir.iterdir() if f.is_file()]
    users = {}
    for f in files:
        with open(f, 'r') as stream:
            users[f.stem] = yaml.load(stream)
    return { "users": users }

async def user(request):
    name = request.match_info['id']
    try:
        with open(f'/cega/users/{name}.yml', 'r') as stream:
            d = yaml.load(stream)
        json_data = { 'password_hash': d.get("password_hash",None), 'pubkey': d.get("pubkey",None), 'expiration': d.get("expiration",None) }
        return web.json_response(json_data)
    except OSError:
        raise web.HTTPBadRequest(text=f'No info for that user {name}... yet\n')

def main():

    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"

    loop = asyncio.get_event_loop()
    server = web.Application(loop=loop)

    template_loader = jinja2.FileSystemLoader("/cega")
    aiohttp_jinja2.setup(server, loader=template_loader)

    # Registering the routes
    server.router.add_get( '/'         , index, name='root')
    server.router.add_get( '/user/{id}', user , name='user')

    # ssl_ctx = ssl.create_default_context(cafile='certs/ca.cert.pem')
    # ssl_ctx.load_cert_chain('certs/cega.cert.pem', 'private/cega.key.pem', password="hello")
    ssl_ctx = None

    # And ...... cue music!
    web.run_app(server, host=host, port=80, shutdown_timeout=0, ssl_context=ssl_ctx, loop=loop)

if __name__ == '__main__':
    main()

