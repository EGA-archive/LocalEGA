import logging
import pika
import uuid
import json

from .conf import CONF

LOG = logging.getLogger('amqp')

def get_connection(domain=None):
    '''
    Returns a blocking connection to the Message Broker supporting AMQP(S).
    
    The host, portm virtual_host, username, password and
    heartbeat values are set from the configuration files.
    So are the SSL options.
    '''
    assert domain in CONF.sections(), "Section not found in config file"

    params = {
        'host': CONF.get(domain,'host',fallback='localhost'),
        'port': CONF.getint(domain,'port',fallback=5672),
        'virtual_host': CONF.get(domain,'vhost',fallback='/'),
        'credentials': pika.PlainCredentials(
            CONF.get(domain,'username'),
            CONF.get(domain,'password')
        ),
        'connection_attempts': CONF.getint(domain,'connection_attempts',fallback=2),
    }
    heartbeat = CONF.getint(domain,'heartbeat', fallback=None)
    if heartbeat is not None: # can be 0
        # heartbeat_interval instead of heartbeat like they say in the doc
        # https://pika.readthedocs.io/en/latest/modules/parameters.html#connectionparameters
        params['heartbeat_interval'] = heartbeat
        LOG.info(f'Setting hearbeat to {heartbeat}')

    # SSL configuration
    if CONF.getboolean(domain,'enable_ssl', fallback=False):
        params['ssl'] = True
        params['ssl_options'] = {
            'ca_certs' : CONF.get(domain,'cacert'),
            'certfile' : CONF.get(domain,'cert'),
            'keyfile'  : CONF.get(domain,'keyfile'),
            'cert_reqs': 2 #ssl.CERT_REQUIRED is actually <VerifyMode.CERT_REQUIRED: 2>
        } 

    LOG.debug(params)

    return pika.BlockingConnection( pika.ConnectionParameters(**params) )


def consume(from_channel, work, from_queue, to_channel=None, to_exchange=None, to_routing=None):
    '''Blocking function, registering callback to be called, on each message from the queue `from_queue`

    If there are no message in `from_queue`, the function blocks and waits for new messages.

    If `routing_to` is supplied, and the function `work` returns a non-None message,
    the new message is published to the exchange with `routing_to` as the routing key.
    '''

    def process_request(channel, method_frame, props, body):
        correlation_id = props.correlation_id
        message_id = method_frame.delivery_tag
        LOG.debug(f'Consuming message {message_id} (Correlation ID: {correlation_id})')

        # Process message in JSON format
        answer = work( json.loads(body) ) # Exceptions should be already caught

        # Publish the answer
        if to_channel and to_exchange and to_routing and answer:
            LOG.debug(f'Replying to {to_routing} with {answer}')
            to_channel.basic_publish(exchange    = to_exchange,
                                     routing_key = to_routing,
                                     properties  = pika.BasicProperties( correlation_id = props.correlation_id ),
                                     body        = json.dumps(answer))
        # Acknowledgment: Cancel the message resend in case MQ crashes
        LOG.debug(f'Sending ACK for message {message_id} (Correlation ID: {correlation_id})')
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    # Let's do this
    from_channel.basic_consume(process_request, queue=from_queue)
    from_channel.start_consuming()

def forward(from_channel, from_queue, to_channel, to_exchange, to_routing, transform=None):
    '''Blocking function, registering callback to be called, on each message from the queue `from_queue`

    If there are no message in `from_queue`, the function blocks and waits for new messages.

    The `transform` parameter accepts a function that takes a message body and returns another message.

    When a message is received, it is passed to transform function and its result to the exchange with the given routing key.
    If transform is None, the received message is sent verbatim to the exchange.
    '''

    assert to_channel and to_exchange and to_routing

    def process_request(channel, method_frame, props, body):
        correlation_id = props.correlation_id
        message_id = method_frame.delivery_tag
        LOG.debug(f'Forwarding message {message_id} (Correlation ID: {correlation_id})')

        if transform:
            body = json.dumps(transform(json.loads(body)))

        # Forward the answer
        to_channel.basic_publish(exchange    = to_exchange,
                                 routing_key = to_routing,
                                 properties  = pika.BasicProperties( correlation_id = props.correlation_id ),
                                 body        = body)
        # Acknowledgment: Cancel the message resend in case MQ crashes
        LOG.debug(f'Sending ACK for message {message_id} (Correlation ID: {correlation_id})')
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    # Let's do this
    from_channel.basic_consume(process_request, queue=from_queue)
    from_channel.start_consuming()

def publish(channel, message, routing_to):
    '''Publish a message to the exchange using a routing key `routing_to`'''

    args = { 'correlation_id': str(uuid.uuid4()),
             'delivery_mode': 2, # make message persistent
    }

    channel.basic_publish(exchange=CONF.get(domain,'exchange', fallback=''),
                          routing_key=routing_to,
                          body=message,
                          properties=pika.BasicProperties(**args))

    LOG.debug(f"Published message to {routing_to}: {message!r}" )

