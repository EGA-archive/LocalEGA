#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Consumes message to update the database with stable IDs to file IDS mappings.

Instead of building a REST endpoint in front of the database, we
exchange messages between the brokers.

Messages will be reliably arrived to the local broker, via the
registered upstream queue.

.. note:: The upstream is registered via an authenticated mechanism, and uses AMQPS.
"""

import sys
import logging

from .utils import db, context
from .utils.amqp import consume, get_connection

LOG = logging.getLogger(__name__)


@db.catch_error
def work(ctx, data):
    """Read a message containing the ids and add it to the database."""
    file_id = data['file_id']
    stable_id = data['stable_id']
    LOG.info(f"Mapping {file_id} to stable_id {stable_id}")

    db.set_stable_id(file_id, stable_id)  # That will flag the entry as 'Ready'

    LOG.info(f"Stable ID {stable_id} mapped to {file_id}")
    return None


def main(args=None):
    """Run mapper service."""
    if not args:
        args = sys.argv[1:]

    ctx = context.Context()
    ctx.setup()  # re-conf

    broker = get_connection('broker')

    # upstream link configured in local broker
    consume(work, ctx, broker, 'stableIDs', None)


if __name__ == '__main__':
    main()
