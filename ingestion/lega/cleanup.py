#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from functools import partial
import os

from crypt4gh.lib import body_decrypt, body_decrypt_parts
from crypt4gh.header import deconstruct, parse

from .conf import CONF
from .utils import db, clean_message
from .utils.amqp import consume, publish

LOG = logging.getLogger(__name__)


def work(inbox_fs, data):
    """Read a message, split the header and decrypt the remainder."""
    job_id = int(data['job_id'])
    LOG.info('Working on job id %s with data %s', job_id, data)

    # Not checking for job cancellation 
    # Marking job as complete
    db.set_status(job_id, 'COMPLETED')  # maybe add more stuff to db that was in message

    # Delete the staged file
    staged_path = data['staged_path']
    LOG.info('Cleaning %s', staged_path)
    try:
        os.remove(staged_path)
    except OSError as oe:
        LOG.warning('Skipping removal of %s, because %s', staged_path, oe)

    # Delete the inbox file ?
    filepath = data['filepath']
    username = data['user']
    LOG.info('Cleaning %s:%s', username, filepath)
    inbox_path = inbox_fs(username, filepath)
    try:
        os.remove(inbox_path)
    except OSError as oe:
        LOG.warning('Skipping removal of %s, because %s', inbox_path, oe)
        

    # Delete empty parent directories, recursively
    # os.walk(), os.rmdir, catch exceptions...
    #
    # Or we just leave them around... they don't take much space

    LOG.debug("Reply message: %s", data)
    
    # Publish the answer
    publish(data)

def main():

    inbox_prefix = CONF.get('inbox', 'location', raw=True)
    def inbox_fs(user, path):
        return os.path.join(inbox_prefix % user, path.strip('/') )

    do_work = partial(work, inbox_fs)

    consume(do_work)


# if __name__ == '__main__':
#     main()
