import logging
import pika
import uuid

from lega.conf import CONF

LOG = logging.getLogger(__name__)
_CONNECTION = None
_CHANNEL = None

def setup():
    global _CONNECTION, _CHANNEL
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
        try:
            # heartbeat_interval instead of heartbeat like they say in the doc
            # https://pika.readthedocs.io/en/latest/modules/parameters.html#connectionparameters
            params['heartbeat_interval'] = CONF.getint('message.broker','heartbeat', fallback=None)
        except KeyError:
            pass

        _CONNECTION = pika.BlockingConnection( pika.ConnectionParameters(**params) )
        _CHANNEL = _CONNECTION.channel()

def process(work):
    def process_request(channel, method_frame, props, body):
        LOG.debug('Consuming Message ID: {}'.format(method_frame.delivery_tag))
        LOG.debug('\tCorrelation ID: {}'.format(props.correlation_id))

        try:
            answer = work(props.correlation_id, body)

            if answer:
                # Send message to response queue
                LOG.debug('\tSuccess: Replying to {} (Correlation ID: {})'.format(props.reply_to, props.correlation_id))
                _CHANNEL.basic_publish(exchange    = CONF.get('message.broker','exchange',fallback='amq.topic'),
                                       routing_key = props.reply_to,
                                       properties  = pika.BasicProperties( correlation_id = props.correlation_id ),
                                       body        = answer)
        except Exception as e:
            # Send message to error queue
            LOG.debug('\tError processing message (Correlation ID: {})\n'.format(props.correlation_id))
            error_msg = '{}: {!r}'.format(e.__class__.__name__, e)
            LOG.debug('\t'+error_msg)
            _CHANNEL.basic_publish(exchange    = CONF.get('message.broker','exchange',fallback='amq.topic'),
                                   routing_key = CONF.get('message.broker','error_queue'),
                                   properties  = pika.BasicProperties( correlation_id = props.correlation_id ),
                                   body        = error_msg)
        finally:
            # Acknowledgment: Cancel the message resend in case MQ crashes
            LOG.debug('\tSending ack for {}'.format(method_frame.delivery_tag))
            _CHANNEL.basic_ack(delivery_tag=method_frame.delivery_tag)
    return process_request


def consume(on_request, from_queue):
    global _CONNECTION, _CHANNEL
    #setup()
    _CHANNEL.basic_qos(prefetch_count=1) # One job per worker
    _CHANNEL.basic_consume(on_request, queue=from_queue)

    try:
        _CHANNEL.start_consuming()
    except KeyboardInterrupt:
        _CHANNEL.stop_consuming()
    finally:
        _CONNECTION.close()
        _CONNECTION = None
        _CHANNEL = None


def publish(message, to_queue, reply_queue=None):
    #setup()
    # _CHANNEL.exchange_declare(exchange=CONF.get('message.broker','exchange',fallback='amq.topic'),
    #                          type='direct')

    args = { 'correlation_id': str(uuid.uuid4()),
             'delivery_mode': 2, # make message persistent
    }
    if reply_queue:
        args['reply_to'] = reply_queue

    _CHANNEL.basic_publish(exchange=CONF.get('message.broker','exchange',fallback='amq.topic'),
                          routing_key=to_queue,
                          body=message,
                          properties=pika.BasicProperties(**args))

    LOG.debug("Published message to {}: {!r}".format(to_queue,message) )
