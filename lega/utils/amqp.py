"""Ensures communication with RabbitMQ Message Broker."""

import logging
import json
import ssl

import pika

from ..conf import CONF
from .logging import _cid

LOG = logging.getLogger(__name__)


def get_connection(domain, blocking=True):
    """Return a blocking connection to the Message Broker supporting AMQP(S).

    The host, portm virtual_host, username, password and
    heartbeat values are read from the CONF argument.
    So are the SSL options.
    """
    LOG.info(f'Getting a connection to {domain}')
    params = CONF.get_value(domain, 'connection', raw=True)
    LOG.debug(f"Initializing a connection to: {params}")
    connection_params = pika.connection.URLParameters(params)

    # Handling the SSL options
    # Note: We re-create the SSL context, so don't pass any ssl_options in the above connection URI.
    if params.startswith('amqps'):

        LOG.debug("Enforcing a TLS context")
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)  # Enforcing (highest) TLS version (so... 1.2?)

        context.verify_mode = ssl.CERT_NONE
        # Require server verification
        if CONF.get_value(domain, 'verify_peer', conv=bool, default=False):
            LOG.debug("Require server verification")
            context.verify_mode = ssl.CERT_REQUIRED
            cacertfile = CONF.get_value(domain, 'cacertfile', default=None)
            if cacertfile:
                context.load_verify_locations(cafile=cacertfile)

        # Check the server's hostname
        server_hostname = CONF.get_value(domain, 'server_hostname', default=None)
        verify_hostname = CONF.get_value(domain, 'verify_hostname', conv=bool, default=False)
        if verify_hostname:
            LOG.debug("Require hostname verification")
            assert server_hostname, "server_hostname must be set if verify_hostname is"
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

        # If client verification is required
        certfile = CONF.get_value(domain, 'certfile', default=None)
        if certfile:
            LOG.debug("Prepare for client verification")
            keyfile = CONF.get_value(domain, 'keyfile')
            context.load_cert_chain(certfile, keyfile=keyfile)

        # Finally, the pika ssl options
        connection_params.ssl_options = pika.SSLOptions(context=context, server_hostname=server_hostname)

    connection_factory = pika.BlockingConnection if blocking else pika.SelectConnection
    return connection_factory(connection_params)


def publish(message, channel, exchange, routing, correlation_id=None):
    """Send a message to the local broker with ``path`` was updated."""
    correlation_id = correlation_id or _cid.get()
    assert(correlation_id), "You should not publish without a correlation id"
    LOG.debug('Sending to exchange: %s [routing key: %s]', exchange, routing, extra={'correlation_id': correlation_id})
    channel.basic_publish(exchange,             # exchange
                          routing,              # routing_key
                          json.dumps(message),  # body
                          properties=pika.BasicProperties(correlation_id=correlation_id,
                                                          content_type='application/json',
                                                          delivery_mode=2))


def consume(work, connection, from_queue, to_routing):
    """Blocking function, registering callback ``work`` to be called.

    from_broker must be a pair (from_connection: pika:Connection, from_queue: str)
    to_broker must be a triplet (to_connection: pika:Connection, to_exchange: str, to_routing: str)

    If there are no message in ``from_queue``, the function blocks and
    waits for new messages.

    If the function ``work`` returns a non-None message, the latter is
    published to the `lega` exchange with ``to_routing`` as the
    routing key.
    """
    assert(from_queue)

    LOG.debug(f'Consuming message from {from_queue}')

    from_channel = connection.channel()
    from_channel.basic_qos(prefetch_count=1)  # One job per worker
    to_channel = connection.channel()

    def process_request(channel, method_frame, props, body):
        try:
            correlation_id = props.correlation_id
            _cid.set(correlation_id)
            message_id = method_frame.delivery_tag
            LOG.debug('Consuming message %s', message_id, extra={'correlation_id': correlation_id})

            # Process message in JSON format
            answer = work(json.loads(body))  # Exceptions should be already caught

            # Publish the answer
            if answer:
                assert(to_routing)
                publish(answer, to_channel, 'lega', to_routing, correlation_id=correlation_id)

            # Acknowledgment: Cancel the message resend in case MQ crashes
            LOG.debug('Sending ACK for message %s', message_id)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        finally:
            _cid.set(None)

    # Let's do this
    try:
        from_channel.basic_consume(from_queue, on_message_callback=process_request)
        from_channel.start_consuming()
    except KeyboardInterrupt:
        from_channel.stop_consuming()
    finally:
        connection.close()
