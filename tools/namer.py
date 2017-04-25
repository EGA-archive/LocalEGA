#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import uuid
from aiohttp import web

LOG = logging.getLogger('namer')

async def new_name(request):
    name = str(uuid.uuid4())
    return web.Response(text=f'{name}\n')

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    server = web.Application()
    server.router.add_get( '/', new_name)
    web.run_app(server, host=host, port=port, shutdown_timeout=0)
