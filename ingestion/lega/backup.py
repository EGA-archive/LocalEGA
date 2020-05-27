#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from functools import partial
import os
import io
import shutil
import hashlib
from pathlib import Path

from .conf import CONF
from .utils import exceptions, db, name2fs, add_prefix, mkdirs
from .utils.amqp import consume, publish

LOG = logging.getLogger(__name__)

@db.check_canceled
def work(destination_fs, data):
    """Backup the pointed file in 2 backend stores."""
    job_id = int(data['job_id'])
    LOG.info('Working on job id %s with data %s', job_id, data)
    LOG.info('Accession id: %s', data['accession_id'])

    source_path = data['staged_path']
    destination_name = name2fs(data['accession_id'])
    destination_path = destination_fs(destination_name)
    md_payload = data['payload_checksum']

    LOG.info('Backing up %s to %s', source_path, destination_path)
    LOG.info('Payload checksum: %s', md_payload)

    # Create parent directories
    mkdirs(destination_path)

    # Copy the source content to the destination
    shutil.copyfile(source_path, destination_path)

    # Easy check: the sizes
    target_size = os.stat(destination_path).st_size
    if( target_size != data['target_size']):
        raise ValueError('Backup failed: files are of different sizes')

    # Re-open to compare checksums
    md = hashlib.new(md_payload['type'])

    with open(destination_path, 'rb') as arfile:
        while True:
            d = arfile.read(1024)
            if not d:
                break
            md.update(d)

    md1 = md.hexdigest()
    md2 = md_payload['value']

    if(md1 != md2):
        LOG.error('Backup failed: different checksums for the payloads')
        LOG.error('* md1: %s', md1)
        LOG.error('* md2: %s', md2)
        raise exceptions.ChecksumsNotMatching(destination_path, md1, md2)

    # All good, record the paths into the (potentially already existing) list
    data['vault_name'] = destination_name
    paths = data.get('mounted_vault_paths', [])
    if paths:
        paths.append(destination_path)
    else:
        data['mounted_vault_paths'] = [destination_path]

    LOG.debug("Reply message: %s", data)

    # Set DB status
    routing_key = CONF.get('DEFAULT', 'routing_key')
    db.set_status(job_id, routing_key.upper())  # the routing key is the database status

    # Publish the answer
    publish(data)

def main():

    # Destination
    destination_prefix = CONF.get('destination', 'location')
    def destination_fs(path):
        return os.path.join(destination_prefix, path.strip('/') )

    do_work = partial(work, destination_fs)

    # upstream link configured in local broker
    os.umask(0o077)  # no group nor world permissions
    consume(do_work)


# if __name__ == '__main__':
#     main()
