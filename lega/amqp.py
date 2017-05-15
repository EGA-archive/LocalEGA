import logging
import pika
import uuid
import json

from .conf import CONF
from . import db
from .exceptions import FromUser as ErrorFromUser

LOG = logging.getLogger('amqp')

def get_connection():
    '''Returns a pair of blocking (connection,channel)
       to the Message Broker supporting AMQP

       The host, portm virtual_host, username, password and
       heartbeat values are set from the configuration files.
    '''

    params = {
        'host': CONF.get('message.broker','host',fallback='localhost'),
        'port': CONF.getint('message.broker','port',fallback=5672),
        'virtual_host': CONF.get('message.broker','vhost',fallback='/'),
        'credentials': pika.PlainCredentials(
            CONF.get('message.broker','username'),
            CONF.get('message.broker','password')
        )
    }
    heartbeat = CONF.getint('message.broker','heartbeat', fallback=None)
    if heartbeat is not None: # can be 0
        # heartbeat_interval instead of heartbeat like they say in the doc
        # https://pika.readthedocs.io/en/latest/modules/parameters.html#connectionparameters
        params['heartbeat_interval'] = heartbeat
        LOG.info(f'Setting hearbeat to {heartbeat}')

    connection = pika.BlockingConnection( pika.ConnectionParameters(**params) )
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker
    return (connection,channel)


def consume(work, from_queue, routing_to=None):
    '''Blocking function, registering callback to be called, on each message from the queue `from_queue`

    If there are no message in `from_queue`, the function blocks and waits for new messages.

    If `routing_to` is supplied, and the function `work` returns a non-None message,
    the new message is published to the exchange with `routing_to` as the routing key.
    '''

    connection, channel = get_connection()
    exchange = CONF.get('message.broker','exchange', fallback='')

    def process_request(channel, method_frame, props, body):
        correlation_id = props.correlation_id
        message_id = method_frame.delivery_tag
        LOG.debug(f'Consuming message {message_id} (Correlation ID: {correlation_id})')

        # Process message in JSON format
        answer = work( json.loads(body) ) # Exceptions should be already caught

        # Publish the answer
        if routing_to and answer:
            LOG.debug(f'Replying to {routing_to} with {answer}')
            channel.basic_publish(exchange    = exchange,
                                  routing_key = routing_to,
                                  properties  = pika.BasicProperties( correlation_id = props.correlation_id ),
                                  body        = answer)
        # Acknowledgment: Cancel the message resend in case MQ crashes
        LOG.debug(f'Sending ACK for message {message_id} (Correlation ID: {correlation_id})')
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    
    # Let's do this
    channel.basic_consume(process_request, queue=from_queue)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


def publish(channel, message, routing_to):
    '''Publish a message to the exchange using a routing key `routing_to`'''

    args = { 'correlation_id': str(uuid.uuid4()),
             'delivery_mode': 2, # make message persistent
    }

    channel.basic_publish(exchange=CONF.get('message.broker','exchange', fallback=''),
                          routing_key=routing_to,
                          body=message,
                          properties=pika.BasicProperties(**args))

    LOG.debug(f"Published message to {routing_to}: {message!r}" )

