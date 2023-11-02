import logging

LOG = logging.getLogger(__name__)

#############################################################
## Consumer 
#############################################################

async def on_message(message, publish_channel):
    correlation_id = message.header.properties.correlation_id
    body = message.body.decode()
    LOG.debug('[%s] %s', correlation_id, body)

