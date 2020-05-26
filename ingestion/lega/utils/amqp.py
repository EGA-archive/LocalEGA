"""Ensures communication with RabbitMQ Message Broker."""

import sys
import os
import logging
import json
import ssl
from socket import gethostname
from pwd import getpwuid
import atexit
from time import sleep


from amqpstorm import (UriConnection, Connection as OrgConnection, Message,
                       AMQPChannelError, AMQPConnectionError, AMQPError)


from ..conf import CONF
from ..conf.logging import _cid
from . import (exceptions, redact_url, clean_message, log_trace)

LOG = logging.getLogger(__name__)


######################################
#        AMQP connection             #
######################################

class AMQPConnection():
    """Initiate AMQP Connection.

    We start 2 channels, one to pull and one to push
    """

    conn = None
    pub_channel = None
    pull_channel = None
    connection_params = None
    ssl_options = None
    interval = None
    attempts = None

    def __init__(self, client_properties=None, conf_section='broker', on_failure=None):
        """Initialize AMQP class."""
        self.on_failure = on_failure
        self.conf_section = conf_section or 'broker'
        # LOG.debug('Conf section', self.conf_section)
        # assert self.conf_section in CONF.sections(), "Section not found in config file"
        pid = os.getpid()
        uid = os.getuid()
        self.client_properties = client_properties or {
            'EGA microservice': {
                'container id': gethostname(),
                'user id': uid,
                'user name': getpwuid(uid).pw_name,
                'process id': pid,
                'process name': self._get_linux_process_name(pid), # docker container => linux
            }
        }
        LOG.debug('Starting an AMQPConnection with %s', self.client_properties)

    def _get_linux_process_name(self, pid):
        with open(f"/proc/{pid}/stat", "rb") as f:
            data = f.read()
            lpar = data.find(b'(')
            rpar = data.find(b')') # data.rfind(b')')
            return data[lpar+1:rpar]

    def fetch_args(self):
        """Retrieve AMQP connection parameters."""
        LOG.debug('Getting a connection to "%s"', self.conf_section)
        params = CONF.getsensitive(self.conf_section, 'connection', raw=True)
        if isinstance(params, bytes):  # secret to str
            params = params.decode()

        self.interval = CONF.getint(self.conf_section, 'try_interval', fallback=1)
        self.attempts = CONF.getint(self.conf_section, 'try', fallback=30)

        LOG.info("Initializing a connection to: %s", redact_url(params))
        self.connection_params =  params

        # Handling the SSL options
        # We create the SSL context, the amqpstorm library will wrap the socket
        if params.startswith('amqps'):

            LOG.debug("Enforcing a TLS context")
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)

            context.verify_mode = ssl.CERT_NONE
            # Require server verification
            if CONF.getboolean(self.conf_section, 'verify_peer', fallback=False):
                LOG.debug("Require server verification")
                context.verify_mode = ssl.CERT_REQUIRED
                cacertfile = CONF.get(self.conf_section, 'cacertfile', fallback=None)
                if cacertfile:
                    context.load_verify_locations(cafile=cacertfile)

            # Check the server's hostname
            server_hostname = CONF.get(self.conf_section, 'server_hostname', fallback=None)
            if CONF.getboolean(self.conf_section, 'verify_hostname', fallback=False):
                LOG.debug("Require hostname verification")
                assert server_hostname, "server_hostname must be set if verify_hostname is"
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED

            # If client verification is required
            certfile = CONF.get(self.conf_section, 'certfile', fallback=None)
            if certfile:
                LOG.debug("Prepare for client verification")
                keyfile = CONF.get(self.conf_section, 'keyfile')
                context.load_cert_chain(certfile, keyfile=keyfile)

            # Finally, the ssl options
            self.ssl_options = { 'context': context, 'server_hostname': server_hostname }

    def connect(self, force=False):
        """Connect to the Message Broker supporting AMQP(S)."""
        if force:
            LOG.debug("Force close the connection")
            self.close()

        if self.conn:
            # LOG.debug("We already have a connection")
            if not self.conn.is_closed:
                # LOG.debug("connection not closed, returning it")
                return
            self.close()

        if not self.connection_params:
            self.fetch_args()

        self.conn = UriConnection(self.connection_params,
                                  ssl_options=self.ssl_options,
                                  client_properties=self.client_properties,
                                  lazy=True) # don't start it

        # Retry loop
        backoff = self.interval
        for count in range(1, self.attempts+1):
            try:
                self.conn.open()
                LOG.debug("Connection successful")
                return
            except AMQPConnectionError as e:
                self.conn.close() # when we can't open, we must close the unused socket
                LOG.error("Opening MQ Connection retry attempt %d", count)
                LOG.error('Reason %r', e)
                sleep(backoff)
                backoff = (2 ** (count // 10)) * self.interval
                # from  0 to  9, sleep 1 * interval secs
                # from 10 to 19, sleep 2 * interval secs
                # from 20 to 29, sleep 4 * interval secs ... etc
        # fail
        if callable(self.on_failure):
            LOG.error("Failed to open the connection")
            self.on_failure()

        
    def close(self):
        """Close MQ channel."""
        LOG.debug("Closing the AMQP connection")
        if self.conn and self.conn.is_open:
            LOG.debug("Closing AMQP socket and channels")
            self.conn.close() # will close all the channels
        self.conn = None
        self.pull_channel = None
        self.pub_channel = None


    # We are reusing the same channel to publish all the messages
    # Consumes goes from the MQ to the client, publish goes from the client to MQ
    # Should we use a session instead? Is it only in AMQP 1.0 ? (amqpstorm is 0.9.1)
    def publish(self, content, exchange, routing_key, correlation_id):
        """Send a message to the local broker exchange using the given routing key."""
        self.connect()
        if self.pub_channel is None:
            self.pub_channel = self.conn.channel()

        LOG.debug('Sending to exchange: %s [routing key: %s]', exchange, routing_key, extra={'correlation_id': correlation_id})
        properties = {
            'correlation_id': correlation_id,
            'content_type': 'application/json',
            'delivery_mode': 2,
        }
        message = Message.create(self.pub_channel, json.dumps(content, indent=4), properties=properties)
        message.publish(routing_key, exchange=exchange)

    def consume(self, queue, process_request):
        """Robust consumer"""
        while True:
            try:
                self.connect()
                if self.pull_channel is None:
                    self.pull_channel = self.conn.channel()
                LOG.info('Consuming message from %s', queue)
                self.pull_channel.basic.qos(prefetch_count=1)  # One job per worker
                self.pull_channel.basic.consume(queue=queue, callback=process_request)
                self.pull_channel.start_consuming()
            except (AMQPChannelError, AMQPConnectionError) as e:
                LOG.error("Retry after %r", e)
                self.close()
            except KeyboardInterrupt:
                LOG.info('Stop consuming (Keyboard Interrupt)')
                if self.pull_channel:
                    self.pull_channel.stop_consuming()
                # self.close() # Not needed. Done by atexit (see below)
                break



######################################
#           Business logic           #
######################################

# Instantiate a global instance
connection = AMQPConnection(on_failure=lambda: sys.exit(1))

atexit.register(lambda: connection.close())

def _handle_request(work, message, content, exchange, error_key):
    # Run the job. There are 4 cases:
    #    * Message rejected by raise RejectMessage inside work
    #    * Malformatted message: ack message, but send to system.error
    #    * User error (FileNotFound, DecryptionError...): ack message, and send to "error queue" (and system.error too)
    #    * All good: ack the message. It's been already sent to the "right queue"
    # Finally, we capture any other/unhandled errors to system.error
    try:
        # Run the job
        work(content)
        # If no exception: we ack
        message.ack()
    except exceptions.RejectMessage as rm:
        LOG.warning('Message %s rejected', message.delivery_tag)
        message.reject() # requeue=True
    except exceptions.FromUser as ue: # ValueError for decryption errors
        cause = ue.__cause__ or ue
        LOG.error('%r', cause)  # repr(cause) = Technical
        assert( isinstance(content, dict) ), "We should have a dict here"
        content['reason'] = str(cause)  # str = Informal
        clean_message(content)
        publish(content, exchange=exchange, routing_key=error_key)
        message.ack()
        raise ue # to send it to error too

def consume(work, ack_on_error=True, threaded=True):
    """Register callback ``work`` to be called, blocking function.

    If there are no message in ``from_queue``, the function blocks and waits for new messages.

    The message is acked if the function ``work`` does not raise an Exception.
    """

    lega_exchange = CONF.get('DEFAULT', 'exchange', fallback='lega')
    from_queue = CONF.get('DEFAULT', 'queue')
    lega_error_key = CONF.get('DEFAULT', 'lega_error', fallback='error')

    cega_exchange = CONF.get('DEFAULT', 'cega_exchange', fallback='cega')
    cega_error_key = CONF.get('DEFAULT', 'cega_error', fallback='files.error')

    # Normally fetch one message at a time (QOS prefetch: 1)
    # So there should be one worker thread at most

    def process_request(message):
        # LOG.debug('Processing message | headers: %s', message.properties)
        correlation_id = message.correlation_id
        message_id = message.delivery_tag
        LOG.info('Processing message')
        _cid.set(correlation_id)  # Normally: data race, if multiple threads. But here, we have 1 worker thread
        LOG.info('Consuming message %s', message_id, extra={'correlation_id': correlation_id})
        content = message.body
        try:
            if message.content_type == 'application/json':
                # Process message in JSON format
                content = json.loads(content)

            if not content: # nothing to do ?
                message.ack() # Force acknowledging the message
                return

            _handle_request(work, message, content, cega_exchange, cega_error_key) # tell Central EGA on error

        except json.JSONDecodeError as je:
            LOG.error('Malformed JSON-message: %s', je, extra={'correlation_id': correlation_id})
            LOG.error('Original message: %s', content, extra={'correlation_id': correlation_id})
            error = {
                'informal': 'Malformed JSON-message',
                'formal': repr(je),
                'message': content,
            }
            # Tell Central EGA
            connection.publish(error,
                               exchange=cega_exchange,
                               routing_key=cega_error_key,
                               correlation_id=correlation_id)
            message.reject(requeue=False)
        except Exception as e:
            # log_trace() # Locate the error
            cause = e.__cause__ or e
            LOG.error('%r', cause)  # repr(cause) = Technical
            content['error'] = {
                'informal': str(cause),
                'formal': repr(cause),
            }
            # Tell Local EGA
            connection.publish(content,
                               exchange=lega_exchange,
                               routing_key=lega_error_key,
                               correlation_id=correlation_id)
            message.reject(requeue=False)
        finally:
            _cid.set(None)
    
    # Run the loop
    try:
        connection.consume(from_queue, process_request)
    except Exception as e:  # Bail out for any other exceptions
        LOG.critical('%r', e)
        log_trace()
        connection.close()
        sys.exit(2)


def publish(content, exchange=None, routing_key=None, correlation_id=None):
    correlation_id = correlation_id or _cid.get()
    assert(correlation_id), "You should not publish without a correlation id"
    exchange = exchange or CONF.get('DEFAULT', 'exchange', fallback='lega')
    routing_key = routing_key or CONF.get('DEFAULT', 'routing_key')
    connection.publish(content, exchange, routing_key, correlation_id)
