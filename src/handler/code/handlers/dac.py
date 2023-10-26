import logging

LOG = logging.getLogger(__name__)

#async def execute(config, message):
#
#    response = await config.db.execute('dac_query', message.content) # use the already formatted data, as json-str
#    LOG.debug('DAC response: %s', response)

async def dataset(config, message):
    response = await config.db.fetchval('on_dac_dataset_update', message.content)
    LOG.debug('DAC-dataset response: %s', response)

async def update(config, message):
    response = await config.db.fetchval('on_dac_update', message.content)
    LOG.debug('DAC update response: %s', response)

async def members(config, message):
    response = await config.db.fetchval('on_dac_members_update', message.content)
    LOG.debug('DAC-user update response: %s', response)
