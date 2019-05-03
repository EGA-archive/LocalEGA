"""Ensures communication with RabbitMQ Message Broker."""

import logging
import pika
import json
import uuid

from ..conf import CONF

LOG = logging.getLogger(__name__)


def get_connection(domain, blocking=True):
    """Return a blocking connection to the Message Broker supporting AMQP(S).

    The host, portm virtual_host, username, password and
    heartbeat values are read from the CONF argument.
    So are the SSL options.
    """
    assert domain in CONF.sections(), "Section not found in config file"

    LOG.info(f'Getting a connection to {domain}')
    params = CONF.get_value(domain, 'connection', raw=True)
    LOG.debug(f"Initializing a connection to: {params}")

    if blocking:
        return pika.BlockingConnection(pika.connection.URLParameters(params))
    return pika.SelectConnection(pika.connection.URLParameters(params))


def publish(message, channel, exchange, routing, correlation_id=None):
    """Send a message to the local broker with ``path`` was updated."""
    LOG.debug(f'Sending to exchange: {exchange} [routing key: {routing}]')
    channel.basic_publish(exchange=exchange,
                          routing_key=routing,
                          body=json.dumps(message),
                          properties=pika.BasicProperties(correlation_id=correlation_id or str(uuid.uuid4()),
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
        correlation_id = props.correlation_id
        message_id = method_frame.delivery_tag
        LOG.debug(f'Consuming message {message_id} (Correlation ID: {correlation_id})')

        # Process message in JSON format
        answer = work(json.loads(body))  # Exceptions should be already caught

        # Publish the answer
        if answer:
            assert(to_routing)
            publish(answer, to_channel, 'lega', to_routing, correlation_id=props.correlation_id)

        # Acknowledgment: Cancel the message resend in case MQ crashes
        LOG.debug(f'Sending ACK for message {message_id} (Correlation ID: {correlation_id})')
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    # Let's do this
    try:
        from_channel.basic_consume(process_request, queue=from_queue)
        from_channel.start_consuming()
    except KeyboardInterrupt:
        from_channel.stop_consuming()
    finally:
        connection.close()
