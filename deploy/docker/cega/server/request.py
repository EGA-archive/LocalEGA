import logging
import json

from aiohttp import web
import aiormq

LOG = logging.getLogger(__name__)

async def grant_permission(request):

    # Make a request and assume it is stored somewhere
    # req = {
    #     "username": username,
    #     "user_id": user_id,
    #     "dataset": dataset_id,
    #     "form_fields": { "comment": "Auto-generated" }
    # }
    # Assume it is granted
    # And send it to the Local EGA

    username = request.match_info.get('username')
    dataset_id = request.match_info.get('dataset_id')
    publish_channel = request.app['mq_channel'] # in our test, it won't be closed.
    users = request.app['users']

    user = users.get(f'{username}-distribution')
    if user is None:
        raise web.HTTPNotFound(reason='User not found')

    # Send permission
    message = {
        "type":"permission",
        "user": user,
        "edited_at":"2023-10-20T10:57:56.981814+00:00",
       "created_at":"2023-10-20T10:57:56.981814+00:00",
       "dataset_id": dataset_id,
       "expires_at": None
    }
    LOG.debug('Sending to FEGA: %s', message)
    await publish_channel.basic_publish(json.dumps(message).encode(),
                                        routing_key='dataset.permission',
                                        exchange='localega',
                                        properties=aiormq.spec.Basic.Properties(delivery_mode=2,
                                                                                content_type='application/json'))
    return web.Response(text='done')
