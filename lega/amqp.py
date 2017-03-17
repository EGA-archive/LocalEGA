import logging
import pika
import uuid

from .conf import CONF

LOG = logging.getLogger(__name__)
_CONNECTION = None
_CHANNEL = None
_EXCHANGE = ''

def setup():
    global _CONNECTION, _CHANNEL, _EXCHANGE
    if not _CONNECTION or not _CHANNEL:
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

        _CONNECTION = pika.BlockingConnection( pika.ConnectionParameters(**params) )
        _CHANNEL = _CONNECTION.channel()
        _CHANNEL.basic_qos(prefetch_count=1) # One job per worker
        _EXCHANGE = CONF.get('message.broker','exchange', fallback='')

        print(_CONNECTION)

def process(work):
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
            _CHANNEL.basic_publish(exchange    = _EXCHANGE,
                                   routing_key = answer_to,
                                   properties  = pika.BasicProperties( correlation_id = props.correlation_id ),
                                   body        = answer)
        # Acknowledgment: Cancel the message resend in case MQ crashes
        LOG.debug('Sending ACK for message {message_id} (Correlation ID: {correlation_id})')
        _CHANNEL.basic_ack(delivery_tag=method_frame.delivery_tag)
    return process_request


def consume(on_request, from_queue):
    global _CONNECTION, _CHANNEL
    _CHANNEL.basic_consume(on_request, queue=from_queue)

    try:
        _CHANNEL.start_consuming()
    except KeyboardInterrupt:
        _CHANNEL.stop_consuming()
    finally:
        _CONNECTION.close()
        _CONNECTION = None
        _CHANNEL = None


def publish(message, routing_to):

    args = { 'correlation_id': str(uuid.uuid4()),
             'delivery_mode': 2, # make message persistent
    }

    _CHANNEL.basic_publish(exchange=_EXCHANGE,
                           routing_key=routing_to,
                           body=message,
                           properties=pika.BasicProperties(**args))

    LOG.debug(f"Published message to {routing_to}: {message!r}" )

