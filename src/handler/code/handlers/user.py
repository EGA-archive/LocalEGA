import logging

LOG = logging.getLogger(__name__)

# message.content: use the already formatted data, as json-str

#async def execute(config, message):
#    response = await config.db.execute('on_user_update', message.content) 
#    LOG.debug('User update response: %s', response)

async def password(config, message):
    response = await config.db.fetchval('on_user_password_update', message.content) 
    LOG.debug('Dataset permission response: %s', response)

async def keys(config, message):
    response = await config.db.fetchval('on_user_keys_update', message.content) 
    LOG.debug('Dataset permission response: %s', response)

async def contact(config, message):
    response = await config.db.fetchval('on_user_contact_update', message.content) 
    LOG.debug('Dataset permission response: %s', response)
