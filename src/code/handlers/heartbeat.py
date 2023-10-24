import logging

LOG = logging.getLogger(__name__)

def execute(config, message):
    LOG.info('Checking heartbeat')

    # publish back that we're alive
    await config.mq.cega_publish(message.body, 'heartbeat')
