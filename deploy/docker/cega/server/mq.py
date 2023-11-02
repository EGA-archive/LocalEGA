import logging
import json

import aiormq

LOG = logging.getLogger(__name__)

EGAF_COUNTER = 0

EGAF = {}

#############################################################
## Consumer 
#############################################################

async def on_message(message, publish_channel, users):
    correlation_id = message.header.properties.correlation_id
    routing_key = message.routing_key
    body = json.loads(message.body.decode())
    LOG.debug('[%s] %s', correlation_id, body)
    LOG.debug('Routing key %s', routing_key)

    if routing_key == 'files.inbox':
        return await send_ingestion(publish_channel, correlation_id, body)
    if routing_key == 'files.verified':
        return await send_accession(publish_channel, correlation_id, body)
    if routing_key == 'files.completed':
        dataset_id = await send_mapping(publish_channel, body)
        await send_dataset_release(publish_channel, dataset_id)
        await send_permission(publish_channel, dataset_id, users)
        return


async def send_ingestion(publish_channel, correlation_id, body):
    message = {
        "type":"ingest",
        "user": body['user'],
        "filepath": body['filepath'],
        "encrypted_checksums": body['encrypted_checksums']
    }
    LOG.debug('Sending to FEGA: [%s] %s', correlation_id, message)
    await publish_channel.basic_publish(json.dumps(message).encode(), routing_key='ingest', exchange='localega', 
                                        properties=aiormq.spec.Basic.Properties(correlation_id=correlation_id))


async def send_accession(publish_channel, correlation_id, body):
    message = {
        "type":"accession",
        "user": body['user'],
        "filepath": body['filepath'],
        "accession_id": getEGAF(body['decrypted_checksums'][0]['value']), 
        "decrypted_checksums": body['decrypted_checksums']
    }

    LOG.debug('Sending to FEGA: [%s] %s', correlation_id, message)
    await publish_channel.basic_publish(json.dumps(message).encode(),routing_key='accession', exchange='localega', 
                                        properties=aiormq.spec.Basic.Properties(correlation_id=correlation_id))


async def send_mapping(publish_channel, body):
    dataset_id = "EGAD90000000123"
    message = {
        "type":"mapping",
        "dataset_id": dataset_id,
        "accession_ids": [ getEGAF(body['decrypted_checksums'][0]['value']) ]
    }
    LOG.debug('Sending to FEGA: %s', message)
    await publish_channel.basic_publish(json.dumps(message).encode(),routing_key='dataset.mapping', exchange='localega')
    return dataset_id


async def send_dataset_release(publish_channel, dataset_id):
    dataset_id = "EGAD90000000123"
    message = {
        "type":"release",
        "dataset_id": dataset_id
    }
    LOG.debug('Sending to FEGA: %s', message)
    await publish_channel.basic_publish(json.dumps(message).encode(),routing_key='dataset.release', exchange='localega')
    return dataset_id


async def send_permission(publish_channel, dataset_id, users):
    message = {
       "type":"permission",
       "user": users['jane-distribution'],
       "edited_at":"2023-10-20T10:57:56.981814+00:00",
       "created_at":"2023-10-20T10:57:56.981814+00:00",
       "dataset_id": dataset_id,
       "expires_at": None
    }
    LOG.debug('Sending to FEGA: %s', message)
    await publish_channel.basic_publish(json.dumps(message).encode(),routing_key='dataset.permission', exchange='localega')


def getEGAF(checksum):
    global EGAF
    global EGAF_COUNTER

    my_egaf = EGAF.get(checksum)
    if my_egaf is None:
        EGAF_COUNTER = EGAF_COUNTER + 1
        my_egaf = f"EGAF9{EGAF_COUNTER:0>11}"
        EGAF[checksum] = my_egaf

    return my_egaf