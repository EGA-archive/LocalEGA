"""
Ensures communication with RabbitMQ Message Broker
"""

import sys
import logging
import pika
import json
from contextlib import contextmanager
import socket
from time import sleep

from ..conf import CONF
from .logging import LEGALogger

LOG = LEGALogger(__name__)

class AMQPConnection():
    conn = None
    chann = None
    args = None

    def __init__(self, conf_section='broker', on_failure=None):
        self.on_failure = on_failure
        self.conf_section = conf_section or 'broker'

    def fetch_args(self):
        assert self.conf_section in CONF.sections(), "Section not found in config file"
        LOG.info('Getting a connection to %s', self.conf_section)
        params = {
            'host': CONF.get_value(self.conf_section, 'host', default='localhost'),
            'port': CONF.get_value(self.conf_section, 'port', conv=int, default=5672),
            'virtual_host': CONF.get_value(self.conf_section, 'vhost', default='/'),
            'credentials': pika.PlainCredentials(
                CONF.get_value(self.conf_section, 'username', default='guest'),
                CONF.get_value(self.conf_section, 'password', default='guest')
            ),
            'connection_attempts': CONF.get_value(self.conf_section, 'connection_attempts', conv=int, default=1),
            'retry_delay': CONF.get_value(self.conf_section,'retry_delay', conv=int, default=10), # seconds
        }
        heartbeat = CONF.get_value(self.conf_section, 'heartbeat', conv=int, default=0)
        if heartbeat is not None:  # can be 0
            # heartbeat_interval instead of heartbeat like they say in the doc
            # https://pika.readthedocs.io/en/latest/modules/parameters.html#connectionparameters
            params['heartbeat_interval'] = heartbeat
            LOG.debug('Setting hearbeat to %s', heartbeat)

        # SSL configuration
        if CONF.get_value(self.conf_section, 'enable_ssl', conv=bool, default=False):
            params['ssl'] = True
            params['ssl_options'] = {
                'ca_certs': CONF.get_value(self.conf_section, 'cacert'),
                'certfile': CONF.get_value(self.conf_section, 'cert'),
                'keyfile':  CONF.get_value(self.conf_section, 'keyfile'),
                'cert_reqs': 2,  # ssl.CERT_REQUIRED is actually <VerifyMode.CERT_REQUIRED: 2>
            }
        LOG.debug(params)
        return params


    def connect(self, blocking=True, force=False):
        '''
        Returns a blocking connection to the Message Broker supporting AMQP(S).
        
        The host, portm virtual_host, username, password and
        heartbeat values are read from the CONF argument.
        So are the SSL options.

        Upon success, the connection is cached.

        Before success, we try to connect ``try`` times every ``try_interval`` seconds (defined in CONF)
        Executes ``on_failure`` after ``try`` attempts.
        '''
        if force:
            self.close()

        if self.conn and self.chann:
            return

        if not self.args:
            self.args = pika.ConnectionParameters(**self.fetch_args())

        connector = pika.BlockingConnection if blocking else pika.SelectConnection

        retry = CONF.get_value(self.conf_section, 'retry', conv=int, default=1)
        retry_delay = CONF.get_value(self.conf_section,'retry_delay', conv=int, default=10) # seconds
        assert retry > 0, "The number of reconnection should be >= 1"
        LOG.debug("%d attempts [interval: %d]", retry, retry_delay)
        count = 0
        while count < retry:
            count += 1
            try:
                LOG.debug("Connection attempt %d", count)
                self.conn = connector(self.args)
                self.chann = self.conn.channel()
                LOG.debug("Connection successful")
                return
            except (pika.exceptions.ProbableAccessDeniedError,
                    pika.exceptions.ProbableAuthenticationError,
                    pika.exceptions.ConnectionClosed,
                    socket.gaierror) as e:
                LOG.debug("MQ connection error: %r", e)
                LOG.debug("Delay %d seconds", retry_delay)
                sleep(retry_delay)
            except Exception as e:
                LOG.debug("Invalid connection: %r", e)
                break

        # fail to connect
        if self.on_failure:
            self.on_failure()
        else:
            LOG.error("Unable to connection to MQ")
            sys.exit(1)

    @contextmanager
    def channel(self):
        if self.conn is None:
            self.connect()
        yield self.chann

    def close(self):
        LOG.debug("Closing the database")
        if self.chann and not self.chann.is_closed and not self.chann.is_closing:
            self.chann.close()
        self.chann = None
        if self.conn and not self.conn.is_closed and not self.conn.is_closing:
            self.conn.close()
        self.conn = None


connection = AMQPConnection()

def publish(message, exchange, routing, correlation_id):
    '''
    Sending a message to the local broker exchange using the given routing key.
    The correlation_id must be specified (and then forwarded).
    '''
    assert( correlation_id )
    LOG.add_correlation_id(correlation_id)
    with connection.channel() as channel:
        LOG.debug('Sending %s to exchange: %s [routing key: %s]', message, exchange, routing)
        channel.basic_publish(exchange    = exchange,
                              routing_key = routing,
                              body        = json.dumps(message),
                              properties  = pika.BasicProperties(correlation_id=correlation_id,
                                                                 content_type='application/json',
                                                                 delivery_mode=2))
    LOG.remove_correlation_id()


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
        LOG.add_correlation_id(correlation_id)

        message_id = method_frame.delivery_tag
        LOG.debug('Consuming message %s', message_id)

        # Process message in JSON format
        answer, error = work(correlation_id, json.loads(body) ) # Exceptions should be already caught

        # Publish the answer
        if answer:
            assert( to_routing )
            publish(answer, 'lega', to_routing, correlation_id=correlation_id)

        # Acknowledgment: Cancel the message resend in case MQ crashes
        if not error or ack_on_error:
            LOG.debug('Sending ACK for message: %s', message_id)
            _channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        LOG.remove_correlation_id()

    # Let's do this
    LOG.debug('MQ setup')
    while True:
        with connection.channel() as channel:
            try:
                LOG.debug('Consuming message from %s', from_queue)
                channel.basic_qos(prefetch_count=1) # One job per worker
                channel.basic_consume(process_request, queue=from_queue)
                channel.start_consuming()
            except KeyboardInterrupt:
                channel.stop_consuming()
                connection.close()
                break
            except (pika.exceptions.ConnectionClosed,
                    pika.exceptions.ConsumerCancelled,
                    pika.exceptions.ChannelClosed,
                    pika.exceptions.ChannelAlreadyClosing,
                    pika.exceptions.AMQPChannelError,
                    pika.exceptions.ChannelError,
                    pika.exceptions.IncompatibleProtocolError) as e:
                LOG.debug('Retrying after %s', e)
                connection.close()
                continue
            # # Note: Let it raise any other exception and bail out.
            # except Exception as e:
            #     LOG.critical('%r', e)
            #     connection.close()
            #     break
            #     #sys.exit(2)
