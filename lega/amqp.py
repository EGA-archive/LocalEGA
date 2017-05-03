import logging
import pika
import uuid

from .conf import CONF

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


def _process(work):
    '''Doc TODO'''
    def process_request(channel, method_frame, props, body):
        correlation_id = props.correlation_id
        message_id = method_frame.delivery_tag
        LOG.debug(f'Consuming message {message_id} (Correlation ID: {correlation_id})')

        try:
            answer = work(props.correlation_id, body)
            answer_to = CONF.get('message.broker','routing_complete')
            LOG.debug(f'Message processed (Correlation ID: {correlation_id})')
        except Exception as e:
            # Send message to error queue
            answer = '{}: {!r}'.format(e.__class__.__name__, e)
            answer_to = CONF.get('message.broker','routing_error')
            LOG.debug('Error processing message (Correlation ID: {correlation_id})\n')


        # Publish the answer
        if answer:
            LOG.debug(f'Replying to {answer_to} (Correlation ID: {correlation_id})')
            channel.basic_publish(exchange    = CONF.get('message.broker','exchange', fallback=''),
                                  routing_key = answer_to,
                                  properties  = pika.BasicProperties( correlation_id = props.correlation_id ),
                                  body        = answer)
        # Acknowledgment: Cancel the message resend in case MQ crashes
        LOG.debug(f'Sending ACK for message {message_id} (Correlation ID: {correlation_id})')
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    return process_request


def consume(work, from_queue):
    '''Blocking function, registering callback to be called, on each message from the queue `from_queue`

    If there are no message in `from_queue`, the function blocks and waits for new messages'''

    connection, channel = get_connection()
    channel.basic_consume(_process(work), queue=from_queue)

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

