#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Worker reading messages from CentralEGA and dispatching to other queues.

The messages are of the following types:
* ``ingest``: the main ingestion job
* ``cancel``: used in case the user cancels an ingestion job
* ``accession``: Receiving an Accession ID from CentralEGA 
* ``mapping``: Receiving a dataset to file mapping (using Accession IDs)
* ``heartbeat``: CentralEGA checking if the LocalEGA instance is alive

"""

import logging

from .conf import CONF
from .conf.logging import _cid
from .utils import db, exceptions, get_sha256
from .utils.amqp import consume, publish

LOG = logging.getLogger(__name__)

def work(data):
    """Read a message, and mark the job as canceled."""

    LOG.info('Working on %s', data)

    correlation_id = _cid.get()
    # should be set
    if not correlation_id:
        raise exceptions.InvalidBrokerMessage('Missing correlation_id. We should have one already set')

    job_type = data.get('type', None)
    if job_type is None:
        raise exceptions.InvalidBrokerMessage('Missing job type: Invalid message')


    if job_type == 'ingest':
        LOG.info('Dispatching an ingestion job for correlation_id %s', correlation_id)
        # correlation_id fetched internally
        job_id = db.insert_job(data['filepath'],
                               data['user'],
                               encrypted_checksums=data.get('encrypted_checksums'))
        
        if job_id == -1:  # no need to work
            LOG.warning('Already ongoing in another message')
            return

        # Otherwise
        data['job_id'] = job_id
        LOG.info('Publish job %d', job_id)
        routing_key = CONF.get('DEFAULT', 'ingest_routing_key', fallback='ingest')
        publish(data, routing_key=routing_key)  # will use the same correlation_id

    elif job_type == 'cancel':
        LOG.info('Canceling job for correlation_id %s', correlation_id)
        # correlation_id fetched internally
        db.cancel_job(data['filepath'],
                      data['user'],
                      encrypted_sha256_checksum=get_sha256(data.get('encrypted_checksums')))

    elif job_type == 'heartbeat':

        LOG.info('Checking heartbeat for correlation_id %s', correlation_id)
        raise NotImplementedError('Heartbeat not implemented yet')

    elif job_type == 'accession':
        
        LOG.info('Receiving an accession id (correlation_id %s)', correlation_id)

        filepath = data.get('filepath')
        user = data.get('user')
        decrypted_sha256 = get_sha256(data.get('decrypted_checksums',[]))
        accession_id = data.get('accession_id')

        # All fields should be there
        if (filepath is None or
            user is None or
            decrypted_sha256 is None or
            accession_id is None):
            raise exceptions.InvalidBrokerMessage('Invalid accession message from CentralEGA')

        # Find the relevant job. Crash if parameters not there
        job = db.find_job(filepath, user, decrypted_sha256)
        
        if job == None:
            LOG.error('No running job for correlation_id %s', correlation_id)
            raise exceptions.RejectMessage(f'No running job for correlation_id {correlation_id}'
                                           f' to associate with Accession ID {accession_id}')

        job_id, staging_info = job
        staging_info['accession_id'] = accession_id
        staging_info.pop('type', None)
        LOG.info('Found job id %s for correlation_id %s and accession_id %s', job_id, correlation_id, accession_id)

        # Sanity check or crash
        assert staging_info['job_id'] == job_id, "Eh? Not the same job_id?"
        assert staging_info['filepath'] == filepath, "Eh? Not the same filepath?"
        assert staging_info['user'] == user, "Eh? Not the same user?"
        assert get_sha256(staging_info['decrypted_checksums']) == decrypted_sha256, "Eh? Not the same decrypted sha256 checksum?"

        # Just record it in the pipeline db
        # db.set_accession_id(job_id, accession_id)
  
        # Republish and let this LocalEGA
        routing_key = CONF.get('DEFAULT', 'accession_routing_key', fallback='accession')
        publish(staging_info, routing_key=routing_key)  # will use the same correlation_id

    elif job_type == 'mapping':

        LOG.info('Receiving a mapping (correlation_id %s)', correlation_id)
        data.pop('type', None)
        # Republish and let the mapper handle it
        routing_key = CONF.get('DEFAULT', 'mapping_routing_key', fallback='save2db')
        publish(data, routing_key=routing_key)  # will use the same correlation_id

    else: # If not caught before, it's not a valid job
        # We reject to message by raising an exception,
        # captured by this LocalEGA's system administrator
        raise exceptions.RejectMessage(f'Invalid operation: {job_type}')
    


def main():
    consume(work)

# if __name__ == '__main__':
#     main()
