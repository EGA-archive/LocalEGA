#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Worker reading messages from the ``files`` queue, splitting the Crypt4GH header from the remainder of the file.

The header is stored in the database and the remainder is sent to the backend storage:
either a regular file system or an S3 object store.

It is possible to start several workers.

When a message is consumed, it must at least contain the following fields:

* ``filepath``
* ``user_id``

Upon completion, a message is sent to the local exchange with the
routing key :``archived``.
"""

import sys
import logging
from pathlib import Path

from legacryptor.crypt4gh import get_header

from .conf import Configuration
from .utils import exceptions, sanitize_user_id, storage
from .utils.amqp import AMQPConnectionFactory
from .utils.worker import Worker
from .utils.db import DB

LOG = logging.getLogger(__name__)


class IngestionWorker(Worker):
    channel = None
    fs = None
    inbox = None

    def __init__(self, fs, inbox, *args, **kwargs):
        self.fs    = fs
        self.inbox = inbox
        super().__init__(*args, **kwargs)
        self.channel = self.amqp_connection.channel()

    def do_work(self, data, correlation_id=None):
        """Read a message, split the header and send the remainder to the backend store."""
        filepath = data['filepath']
        LOG.info(f"[correlation_id={correlation_id}] Processing {filepath}")

        # Remove the host part of the user name
        user_id = sanitize_user_id(data['user'])

        # TODO Remove this strangeness once the new code is finished.
        # Keeping data as-is (cuz the decorator is using it)
        # It will be augmented, but we keep the original data first
        org_msg = data.copy()
        data['org_msg'] = org_msg

        # Insert in database
        LOG.debug(f"[correlation_id={correlation_id}] Inserting {filepath} into database")
        file_id = self.db.insert_file(filepath, user_id)
        data['file_id'] = file_id  # must be there: database error uses it

        LOG.debug(f"[correlation_id={correlation_id}] File id of {filepath} is {file_id}")

        # Find inbox
        inbox = Path(self.inbox % user_id)
        LOG.info(f"[correlation_id={correlation_id}] Inbox area: {inbox}")

        # Check if file is in inbox
        inbox_filepath = inbox / filepath.lstrip('/')
        LOG.info(f"[correlation_id={correlation_id}] Inbox file path: {inbox_filepath}")
        if not inbox_filepath.exists():
            raise exceptions.NotFoundInInbox(filepath)  # return early

        # Ok, we have the file in the inbox

        # Record in database
        self.db.mark_in_progress(file_id)

        # Sending a progress message to CentralEGA
        self.report_to_cega({**data, "status": "PROCESSING"}, 'files.processing')

        # Strip the header out and copy the rest of the file to the vault
        LOG.debug(f'[correlation_id={correlation_id}] Opening {inbox_filepath}')
        with open(inbox_filepath, 'rb') as infile:
            LOG.debug(f'[correlation_id={correlation_id}] Reading header | file_id: {file_id}')
            beginning, header = get_header(infile)

            header_hex = (beginning+header).hex()
            data['header'] = header_hex
            self.db.store_header(file_id, header_hex)  # header bytes will be .hex()

            LOG.info("f[correlation_id={correlation_id}] Getting the location of {file_id}")
            target = self.fs.location(file_id)
            LOG.info(f'[correlation_id={correlation_id}] [{self.fs.__class__.__name__}] Moving the rest of {filepath} to {target}')
            target_size = self.fs.copy(infile, target)  # It will copy the rest only

            LOG.info(f'[correlation_id={correlation_id}] Vault copying completed. Updating database')
            self.db.set_archived(file_id, target, target_size)
            data['vault_path'] = target

        LOG.debug(f"[correlation_id={correlation_id}] Reply message: {data}")
        return data


def main(args=None):
    """Run ingest service."""
    if not args:
        args = sys.argv[1:]

    conf = Configuration()
    conf.setup(args)
    dbargs = conf.get_db_args('postgres')
    db = DB(**dbargs)

    fs = getattr(storage, conf.get_value('vault', 'driver', default='FileStorage'))(conf)

    amqp_cf = AMQPConnectionFactory(conf, 'broker')
    broker = amqp_cf.get_connection()
    inbox = conf.get_value('inbox', 'location', raw=True)

    worker = IngestionWorker(fs=fs, inbox=inbox, db=db, amqp_connection=broker)
    worker.run('files', 'archived')


if __name__ == '__main__':
    main()
