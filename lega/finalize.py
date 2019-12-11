#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Consumes message to update the database with stable IDs to file IDS mappings.

Instead of building a REST endpoint in front of the database, we
exchange messages between the brokers.

Messages will be reliably arrived to the local broker, via the
registered upstream queue.

.. note:: The upstream is registered via an authenticated mechanism, and uses AMQPS.
"""

import logging

from .conf import configure
from .utils import db, errors
from .utils.amqp import consume

LOG = logging.getLogger(__name__)


@errors.catch(ret_on_error=(None, True))
def work(data):
    """Read a message containing the ids and add it to the database."""
    file_id = data['file_id']
    stable_id = data['stable_id']
    LOG.info("Mapping file_id %s to stable_id %s", file_id, stable_id)

    # Remove file from the inbox
    # TODO

    db.set_stable_id(file_id, stable_id)  # That will flag the entry as 'Ready'

    LOG.info("Stable ID %s mapped to %s", stable_id, file_id)
    return (None, False)


@configure
def main():
    """Listen for incoming stable IDs."""
    # upstream link configured in local broker
    consume(work, broker, 'stableIDs', None)


if __name__ == '__main__':
    main()
