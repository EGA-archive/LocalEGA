import logging

LOG = logging.getLogger(__name__)

# message.content: use the already formatted data, as json-str

async def execute(config, message):
    response = await config.db.fetchval('on_dataset_mapping', message.content) 
    LOG.debug('Dataset mapping response: %s', response)

async def release(config, message):
    response = await config.db.fetchval('on_dataset_release', message.content) # use the already formatted data, as json-str
    LOG.debug('Dataset release response: %s', response)
    if not response:
        raise ValueError('Nothing released: Probably missing dataset')

async def deprecate(config, message):
    response = await config.db.fetchval('on_dataset_deprecated', message.content) # use the already formatted data, as json-str
    LOG.debug('Dataset deprecate response: %s', response)
    if not response:
        raise ValueError('Nothing released: Probably missing dataset')
    # Note: this could further trigger a dataset deletion from the Vault

async def permission(config, message):
    response = await config.db.fetchval('on_granted_permission', message.content) 
    LOG.debug('Dataset permission response: %s', response)

async def delete_permission(config, message):
    response = await config.db.fetchval('on_revoked_permission', message.content) 
    LOG.debug('Dataset delete permission response: %s', response)
