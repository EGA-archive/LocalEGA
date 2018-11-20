#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Mirroring the index files from the inbox location to the NFS mounted index location.

When a message is consumed, it must at least contain the following fields:

* ``filepath``
* ``user_id``

Upon completion, a message is sent to the local exchange with the
routing key :``index-mirrored``.
'''

import sys
from pathlib import Path
import shutil

from .conf import CONF, configure
from .utils import exceptions, sanitize_user_id
from .utils.amqp import consume, publish
from .utils.logging import LEGALogger

LOG = LEGALogger(__name__)

def _work(correlation_id, data):
    '''Reads a message, splits the header and sends the remainder to the backend store.'''

    # Adding correlation ID to context
    LOG.add_correlation_id(correlation_id)

    # Use user_id, and not elixir_id
    user_id = sanitize_user_id(data['user'])
    filepath = data['file_path']

    # Find storage locations
    inbox = Path(CONF.get_value('inbox', 'location', raw=True) % user_id)
    LOG.info("Inbox area: %s", inbox)
    index = Path(CONF.get_value('index', 'location', raw=True) % user_id)
    LOG.info("Index area: %s", index)

    # Check if file is in inbox
    inbox_filepath = inbox / filepath.lstrip('/')
    LOG.info("Inbox file path: %s", inbox_filepath)

    if not inbox_filepath.exists():
        raise exceptions.NotFoundInInbox(filepath) # return early

    index_filepath = index / filepath.lstrip('/')
    LOG.info("Index file path: %s", index_filepath)

    # Copying the file over to NFS
    index_filepath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(inbox_filepath), str(index_filepath), follow_symlinks=False)

    LOG.debug("Reply message: %s", data)
    LOG.remove_correlation_id()
    return (data, False)

@configure
def main():

    # upstream link configured in local broker
    consume(_work, 'indices', 'index-mirrored')

if __name__ == '__main__':
    main()
