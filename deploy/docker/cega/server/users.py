import logging

from base64 import b64decode
import json

from aiohttp import web

LOG = logging.getLogger(__name__)

HTTP_AUTH_USERNAME = 'fega'
HTTP_AUTH_PASSWORD = 'testing' # yup, we don't care, it's just for testing

async def get_user(request):

    # Authenticate
    auth_header = request.headers.get('AUTHORIZATION')
    if not auth_header:
        raise web.HTTPUnauthorized(reason='Protected access')
    _, token = auth_header.split(None, 1)  # Skipping the Basic keyword
    auth_user, auth_password = b64decode(token).decode().split(':', 1)
    if HTTP_AUTH_USERNAME != auth_user or HTTP_AUTH_PASSWORD != auth_password:
        raise web.HTTPUnauthorized(reason='Protected access')

    # Search
    term = request.match_info.get('term')
    record = request.app['users'].get(term)

    if not record:
        raise web.HTTPNotFound(reason='User not found')

    return web.json_response(record,
                             headers = { "Server": "Central EGA (test) Server",
                                         "X-EGA-apiVersion" : "v2",
                                         "X-EGA-docLink" : "https://ega-archive.org",
                                        })

def load_users(filepath):
    users = {}
    with open(filepath, 'r') as stream:
        users = json.load(stream)
    LOG.debug('Loaded %d users: %s', len(users) / 2, list(users.keys()))
    return users
