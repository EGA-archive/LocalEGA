"""
Ensures communication with RabbitMQ Message Broker
"""

import logging
import pika
import json
import uuid

from ..conf import CONF

LOG = logging.getLogger(__name__)

connection = None

def get_connection(domain, blocking=True):
    '''
    Returns a blocking connection to the Message Broker supporting AMQP(S).

    The host, portm virtual_host, username, password and
    heartbeat values are read from the CONF argument.
    So are the SSL options.
    '''
    assert domain in CONF.sections(), "Section not found in config file"

    params = {
        'host': CONF.get_value(domain, 'host', default='localhost'),
        'port': CONF.get_value(domain, 'port', conv=int, default=5672),
        'virtual_host': CONF.get_value(domain, 'vhost', default='/'),
        'credentials': pika.PlainCredentials(
            CONF.get_value(domain, 'username', default='guest'),
            CONF.get_value(domain, 'password', default='guest')
        ),
        'connection_attempts': CONF.get_value(domain, 'connection_attempts', conv=int, default=10),
        'retry_delay': CONF.get_value(domain,'retry_delay', conv=int, default=10), # seconds
    }
    heartbeat = CONF.get_value(domain, 'heartbeat', conv=int, default=0)
    if heartbeat is not None:  # can be 0
        # heartbeat_interval instead of heartbeat like they say in the doc
        # https://pika.readthedocs.io/en/latest/modules/parameters.html#connectionparameters
        params['heartbeat_interval'] = heartbeat
        LOG.debug(f'Setting hearbeat to {heartbeat}')

    # SSL configuration
    if CONF.get_value(domain, 'enable_ssl', conv=bool, default=False):
        params['ssl'] = True
        params['ssl_options'] = {
            'ca_certs': CONF.get_value(domain, 'cacert'),
            'certfile': CONF.get_value(domain, 'cert'),
            'keyfile':  CONF.get_value(domain, 'keyfile'),
            'cert_reqs': 2,  # ssl.CERT_REQUIRED is actually <VerifyMode.CERT_REQUIRED: 2>
        }

    LOG.info(f'Getting a connection to {domain}')
    LOG.debug(params)

    if blocking:
        return pika.BlockingConnection(pika.ConnectionParameters(**params))
    return pika.SelectConnection(pika.ConnectionParameters(**params))

def close():
    global channel
    global connection
    if channel and not channel.is_closed and not channel.is_closing:
        channel.close()
    channel = None
    if connection and not connection.is_closed and not connection.is_closing:
        connection.close()
    connection = None

def open_channel(force_reconnect=False):
    global channel
    global connection
    if connection is None or channel is None:
        LOG.debug('Opening connection to local broker')
        connection = get_connection('broker')
        channel = connection.channel()
    

def publish(message, exchange, routing, correlation_id=None):
    '''
    Sending a message to the local broker with ``path`` was updated
    '''
    open_channel()
    LOG.debug(f'Sending {message} to exchange: {exchange} [routing key: {routing}]')
    channel.basic_publish(exchange    = exchange,
                          routing_key = routing,
                          body        = json.dumps(message),
                          properties  = pika.BasicProperties(correlation_id=correlation_id or str(uuid.uuid4()),
                                                             content_type='application/json',
                                                             delivery_mode=2))

def consume(work, from_queue, to_routing, ack_on_error=True):
    '''Blocking function, registering callback ``work`` to be called.

    from_broker must be a pair (from_connection: pika:Connection, from_queue: str)
    to_broker must be a triplet (to_connection: pika:Connection, to_exchange: str, to_routing: str)

    If there are no message in ``from_queue``, the function blocks and
    waits for new messages.

    If the function ``work`` returns a non-None message, the latter is
    published to the `lega` exchange with ``to_routing`` as the
    routing key.
    '''

    assert( from_queue )

    def process_request(_channel, method_frame, props, body):
        correlation_id = props.correlation_id
        message_id = method_frame.delivery_tag
        LOG.debug(f'Consuming message {message_id} (Correlation ID: {correlation_id})')

        # Process message in JSON format
        answer, error = work( json.loads(body) ) # Exceptions should be already caught

        # Publish the answer
        if answer:
            assert( to_routing )
            publish(answer, 'lega', to_routing, correlation_id = props.correlation_id)

        # Acknowledgment: Cancel the message resend in case MQ crashes
        if not error or ack_on_error:
            LOG.debug(f'Sending ACK for message {message_id} (Correlation ID: {correlation_id})')
            _channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    # Let's do this
    LOG.debug(f'Consuming message from {from_queue}')
    while True:
        open_channel() # might raise exception
        try:
            channel.basic_qos(prefetch_count=1) # One job per worker
            channel.basic_consume(process_request, queue=from_queue)
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
        except pika.exceptions.ConnectionClosed as e:
            LOG.debug('Retrying after %s', e)
            close()
            continue
        break

    close()


def tell_cega(message, status):
    message['status'] = status
    LOG.debug(f'Sending message to CentralEGA: {message}')
    publish(message, 'cega', 'files.processing')
    message.pop('status', None)
