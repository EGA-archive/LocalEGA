import sys
import logging
import asyncio
import json
from socket import gethostname
from pwd import getpwuid
import os
import ssl

import aiormq
import pamqp
from yarl import URL

CONNECTION_EXCEPTIONS = (
    RuntimeError,
    ConnectionError,
    OSError,
    aiormq.exceptions.AMQPError,
    asyncio.CancelledError,
    pamqp.exceptions.PAMQPException
) + tuple(
    pamqp.exceptions.CLASS_MAPPING.values(),
)

LOG = logging.getLogger(__name__)

class MQConnection():
    """ Connection abstraction """

    __slots__ = (
        'connection',
        'consumer',
        'publisher',
        'lock',
        'conf',
        'conf_section',
        'ssl_options',
        'connection_params',
        'connection_properties'
    )

    def __init__(self, conf, conf_section='broker'):
        self.connection = None
        self.consumer = None # aiormq.Channel
        self.publisher = None # aiormq.Channel
        self.lock = asyncio.Lock()
        self.conf = conf
        self.conf_section = conf_section
        
    def fetch_args(self):
        """Retrieve AMQP connection parameters."""
        self.connection_params = self.conf.getsensitive(self.conf_section, 'connection', raw=True)
        if isinstance(self.connection_params, bytes):  # secret to str
            self.connection_params = self.connection_params.decode()

        self.connection_properties={ "connection_name": self.conf.get(self.conf_section, 'connection_name'),
                                     'FEGA_handler': {
                                         'hostname': gethostname(), # container id or hostname
                                         'user_id': os.getuid(),
                                         'user_name': getpwuid(os.getuid()).pw_name,
                                         'process_id': os.getpid(),
                                         'process_name': 'fega_handler',
                                     }
                                    }


        # Handling the SSL options
        # We create the SSL context, the amqpstorm library will wrap the socket
        if self.connection_params.startswith('amqps'):

            LOG.debug("Enforcing a TLS context")
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)

            context.verify_mode = ssl.CERT_NONE
            # Require server verification
            if self.conf.getboolean(self.conf_section, 'verify_peer', fallback=False):
                LOG.debug("Require server verification")
                context.verify_mode = ssl.CERT_REQUIRED
                cacertfile = self.conf.get(self.conf_section, 'cacertfile', fallback=None)
                if cacertfile:
                    context.load_verify_locations(cafile=cacertfile)

            # Check the server's hostname
            server_hostname = self.conf.get(self.conf_section, 'server_hostname', fallback=None)
            if self.conf.getboolean(self.conf_section, 'verify_hostname', fallback=False):
                LOG.debug("Require hostname verification")
                assert server_hostname, "server_hostname must be set if verify_hostname is"
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED

            # If client verification is required
            certfile = self.conf.get(self.conf_section, 'certfile', fallback=None)
            if certfile:
                LOG.debug("Prepare for client verification")
                keyfile = self.conf.get(self.conf_section, 'keyfile')
                context.load_cert_chain(certfile, keyfile=keyfile)

            # Finally, the ssl options
            self.ssl_options = { 'context': context, 'server_hostname': server_hostname }

    def __str__(self):
        return str(self.connection) if self.connection else "MQConnection"

    def __repr__(self):
        return '<{0}: "{1}">'.format(self.__class__.__name__, str(self))

    async def connect(self):
        self.fetch_args()
        async with self.lock:
            self.connection = aiormq.Connection(self.connection_params)
            LOG.info('Connection to %s', self.connection.url.with_password('****'))
            await self.connection.connect(self.connection_properties)
            LOG.debug('Creating the consumer and publisher channels')
            self.consumer = await self.connection.channel()
            self.publisher = await self.connection.channel()

    async def consume(self, on_message):
        if self.consumer is None:
            await self.connect()
        if self.consumer.is_closed:
            LOG.debug("Consumer Channel closed: reconnecting")
            await asyncio.gather(self.connection.close(), return_exceptions=False)
            self.consumer = None
            await self.connect()

        LOG.debug('QOS to 1')
        await self.consumer.basic_qos(prefetch_count=1)
        queue = self.conf.get(self.conf_section, 'queue')
        LOG.debug('Start consuming from %s', queue)
        assert queue, "No queue specified"
        return await self.consumer.basic_consume(queue, on_message)

    async def publish(self, message, exchange, routing_key, correlation_id=None, timeout=None):
        LOG.debug("Publishing to exchange: %s [routing key: %s]", exchange, routing_key)
        try:
            if self.publisher is None:
                LOG.debug("First connecting")
                await self.connect()
            if self.publisher.is_closed:
                LOG.debug("Publisher Channel closed: reconnecting")
                await asyncio.gather(self.connection.close(), return_exceptions=False)
                self.publisher = None
                await self.connect()

            if self.publisher is None:
                return False

            properties = {
                'delivery_mode': 2,
                'content_type': 'text/plain',
            }
            if correlation_id:
                properties['correlation_id'] = correlation_id

            _message = message
            if not (isinstance(_message, str) or isinstance(_message, bytes)):
                _message = json.dumps(_message, indent=4)
                properties['content_type']='application/json'

            if not isinstance(message, bytes):
                _message = _message.encode()

            await self.publisher.basic_publish(_message,
                                               exchange=exchange,
                                               routing_key=routing_key,
                                               properties=aiormq.spec.Basic.Properties(**properties)
                                               )
            return True
        except aiormq.exceptions.ProbableAuthenticationError as e:
            LOG.error('Authentication Error: %s', e)
            return False
        except CONNECTION_EXCEPTIONS as e:
            LOG.warning('Connection attempt to "%s" failed. ', self)
            LOG.error('%r', e)
            # Cleanup
            await asyncio.gather(self.connection.close(e), return_exceptions=False)
            del self.publisher
            self.publisher = None # Channel will be close
            return False
        except Exception as e:
            LOG.error("Message not sent: %r", e)
            return False

    async def lega_publish(self, message, routing_key, **kwargs):
        exchange = self.conf.get(self.conf_section, 'lega_exchange')
        await self.publish(message, exchange, routing_key, **kwargs)

    async def cega_publish(self, message, routing_key, **kwargs):
        exchange = self.conf.get(self.conf_section, 'cega_exchange')
        await self.publish(message, exchange, routing_key, **kwargs)


