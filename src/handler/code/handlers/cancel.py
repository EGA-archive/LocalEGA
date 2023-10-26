import logging

from . import clean_staging

LOG = logging.getLogger(__name__)

async def execute(config, message):

    clean_staging(config, message.parsed)
    


