import logging
import json

import aiormq

LOG = logging.getLogger(__name__)

EGAF_COUNTER = 0

EGAD = "EGAD90000000123"
EGAF = {} # checksum -> accession id

async def mq_send(publish_channel, message, routing_key, properties=None):
    return await publish_channel.basic_publish(json.dumps(message).encode(),
                                               routing_key=routing_key,
                                               exchange='localega',
                                               properties=properties)

def get_file_accession(checksum):
    global EGAF
    global EGAF_COUNTER
    accession_id = EGAF.get(checksum)
    if accession_id is None:
        EGAF_COUNTER = EGAF_COUNTER + 1
        accession_id = f"EGAF9{EGAF_COUNTER:0>11}"
        EGAF[checksum] = accession_id
    return accession_id

async def on_message(message, publish_channel):
    correlation_id = message.header.properties.correlation_id
    routing_key = message.routing_key
    body = json.loads(message.body.decode())
    LOG.debug('[%s] %s', correlation_id, body)
    LOG.debug('Routing key %s', routing_key)

    if routing_key == 'files.inbox':
        operation = body['operation']
        if operation == 'upload':
            return await send_ingestion(publish_channel, correlation_id, body)
        if operation == 'remove':
            return await send_cancel(publish_channel, correlation_id, body)
        if operation == 'rename':
            LOG.debug('Rename: do nothing')
            return
        raise ValueError(f'Invalid operation: {operation}')
    if routing_key == 'files.verified':
        return await send_accession(publish_channel, correlation_id, body)
    if routing_key == 'files.completed':
        dataset_id = await send_mapping(publish_channel, body)
        await send_dataset_release(publish_channel, dataset_id)
        return


async def send_ingestion(publish_channel, correlation_id, body):
    message = {
        "type":"ingest",
        "user": body['user'],
        "filepath": body['filepath'],
        "encrypted_checksums": body['encrypted_checksums']
    }
    LOG.debug('Sending to FEGA: [%s] %s', correlation_id, message)
    await mq_send(publish_channel, message, 'ingest',
                  properties=aiormq.spec.Basic.Properties(correlation_id=correlation_id))

async def send_cancel(publish_channel, correlation_id, body):
    message = {
        "type":"cancel",
        "user": body['user'],
        "filepath": body['filepath'],
        #"encrypted_checksums": body['encrypted_checksums']
    }
    LOG.debug('Sending to FEGA: [%s] %s', correlation_id, message)
    await mq_send(publish_channel, message, 'cancel',
                  properties=aiormq.spec.Basic.Properties(correlation_id=correlation_id))


async def send_accession(publish_channel, correlation_id, body):
    message = {
        "type":"accession",
        "user": body['user'],
        "filepath": body['filepath'],
        "accession_id": get_file_accession(body['decrypted_checksums'][0]['value']), 
        "decrypted_checksums": body['decrypted_checksums']
    }

    LOG.debug('Sending to FEGA: [%s] %s', correlation_id, message)
    await mq_send(publish_channel, message, 'accession',
                  properties=aiormq.spec.Basic.Properties(correlation_id=correlation_id))


async def send_mapping(publish_channel, body):
    global EGAD
    message = {
        "type":"mapping",
        "dataset_id": EGAD,
        "accession_ids": [ get_file_accession(body['decrypted_checksums'][0]['value']) ]
    }
    LOG.debug('Sending to FEGA: %s', message)
    await mq_send(publish_channel, message, 'dataset.mapping')
    return EGAD


async def send_dataset_release(publish_channel, dataset_id):
    message = {
        "type":"release",
        "dataset_id": dataset_id
    }
    LOG.debug('Sending to FEGA: %s', message)
    await mq_send(publish_channel, message, 'dataset.release')




