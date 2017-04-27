#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
from pathlib import Path
from aiohttp import web

LOG = logging.getLogger('namer')

COUNTER = Path(__file__).parent / 'namer.counter'

def set_count(c):
    with open(COUNTER, 'w') as f:
        f.write(str(c))

def get_count():
    if not COUNTER.exists():
        set_count(0)

    with open(COUNTER, 'r') as f:
        return int(f.read())

async def new_name(request):
    c = get_count() + 1
    name = '{0:021d}'.format(c)
    set_count(c)
    return web.Response(text=f'{name}\n')

if __name__ == '__main__':
    server = web.Application()
    server.router.add_get( '/', new_name)
    web.run_app(server, shutdown_timeout=0,
                host = sys.argv[1] if len(sys.argv) > 1 else 'localhost',
                port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080)
