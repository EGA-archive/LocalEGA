#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Worker storing mappings into the storage database.

"""

import logging

from psycopg2 import sql

from .conf import CONF
from .conf.logging import _cid
from .utils import db, exceptions, clean_message, get_sha256
from .utils.amqp import consume, publish

LOG = logging.getLogger(__name__)


def save_file_to_db(correlation_id, data):
    filepath = data['filepath']
    username = data['user']
    accession_id = data['accession_id']
    decrypted_checksums = data['decrypted_checksums'] # must be there
    paths = data['mounted_vault_paths']
    assert len(paths or []) > 1

    encrypted_checksums = data.get('encrypted_checksums', [])
    encrypted_checksum = None
    encrypted_checksum_type = None
    for c in encrypted_checksums:
        if c.get('type').upper() == 'SHA256':
            encrypted_checksum = c['value']
            encrypted_checksum_type = 'SHA256'
            break

    if not encrypted_checksum and encrypted_checksums: 
        c = encrypted_checksums[0] # pick the first one
        encrypted_checksum = c['value']
        encrypted_checksum_type = c['type'].upper()

    # Save to DB
    # Here we use an example DB. Each LocalEGA can implement their own schema
    # and update the query below
    with db.connection.cursor() as cur:
        cur.execute('''INSERT INTO local_ega.main (correlation_id,inbox_user,inbox_path,
                                                   inbox_path_encrypted_checksum,
                                                   inbox_path_encrypted_checksum_type,
                                                   inbox_path_size,header,payload_size,
                                                   payload_checksum, decrypted_checksum, accession_id,
                                                   payload_path, payload_path2) 
                           VALUES (%(correlation_id)s,%(inbox_user)s,%(inbox_path)s,
                                   %(enc_cs)s,%(enc_cs_t)s,%(inbox_path_size)s,
                                   %(header)s,%(payload_size)s,%(payload_cs)s,
                                   %(decrypted_cs)s,%(accession_id)s,%(payload_path)s,%(payload_path2)s);''',
                    {'correlation_id': correlation_id,
                     'inbox_user': username,
                     'inbox_path': filepath,
                     'enc_cs': encrypted_checksum,
                     'enc_cs_t': encrypted_checksum_type,
                     'inbox_path_size': data.get('filesize'),
                     'header': data['header'],
                     'payload_size': data['target_size'],
                     'payload_cs': data['payload_checksum']['value'],
                     'decrypted_cs': get_sha256(decrypted_checksums),
                     'accession_id': data['accession_id'],
                     'payload_path': 'file://' + paths[0],
                     'payload_path2': 'file://' + paths[1],
                    })

def save_mapping_to_db(correlation_id, data):
    dataset_id = data['dataset_id']
    accession_ids = data['accession_ids']
    assert accession_ids # aka accession_ids is not None and len(accession_ids) > 0

    # Save mapping to DB: the file should already exist.
    # Here we use an example DB.
    # Each LocalEGA can implement their own schema and update the query below
    with db.connection.cursor() as cur:
        cur.execute('''UPDATE local_ega.main 
                       SET dataset_id = %(dataset_id)s
                       WHERE accession_id = ANY(%(accession_ids)s);''',
                    { 'dataset_id': dataset_id,
                      'accession_ids': accession_ids
                     })
        

def work(data):

    LOG.info('Working on %s', data)

    correlation_id = _cid.get()
    # should be set
    if not correlation_id:
        raise exceptions.InvalidBrokerMessage('Missing correlation_id. We should have one already set')

    job_type = data.get('type', None)

    if job_type == 'accession':
        LOG.info('Receiving an ingestion command (correlation_id %s)', correlation_id)
        save_file_to_db(correlation_id, data)
        clean_message(data)
        publish(data)  # will publish to cega, use the same correlation_id
        return

    if job_type == 'mapping':
        LOG.info('Receiving a mapping (correlation_id %s)', correlation_id)
        save_mapping_to_db(correlation_id, data)
        #publish(data)  # will publish to cega, use the same correlation_id
        return

    # Otherwise
    raise exceptions.InvalidBrokerMessage(f'Invalid job type: {job_type}')


def main():
    consume(work)
