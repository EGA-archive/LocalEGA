import sys
import logging
import traceback
import json

from functools import partial, wraps
from ..utils import db
from .amqp import publish, AMQPConnectionFactory
from .exceptions import FromUser

LOG = logging.getLogger(__name__)

class Worker(object):
    db   = None
    amqp_connection = None
    channel = None # TODO remove this in future

    def __init__(self, db, amqp_connection):
        assert db is not None, "Database connection is needed"
        assert amqp_connection is not None, "AMQP Connection is needed"
        self.db = db
        self.amqp_connection = amqp_connection
        self.channel = amqp_connection.channel()

    def worker(self, data):
        # TODO Do error logging in THIS function instead of wrapping it like this
        func = db.crypt4gh_to_user_errors(self.do_work)
        try:
            return func(data)
        except AssertionError as e:
            raise e
        except Exception as e:
            file_id = data.get('file_id', None)
            cause = e.__cause__ or e
            if file_id:
                self.db.set_error(file_id, cause, isinstance(e, FromUser))
            if not isinstance(e, FromUser):
                return None

            LOG.debug('Catching error on file id: %s', file_id)
            org_msg = data.pop('org_msg', None)  # should be there
            org_msg['reason'] = str(cause)  # str = Informal

            LOG.info(f'Sending user error to local broker: {org_msg}')

            ## TODO This is the part where we are supposed to report errors back
            ## somehow. Would be nice if it could be done smoother.
            try:
                self.report_to_cega(org_msg, 'files.error')
            except Exception as e2:
                LOG.error(f'While handling "{e}", we caught "{e2!r}"')
                print(repr(e), 'caused', repr(e2), file=sys.stderr)
        return None

    def report_to_cega(self, message, queue):
        publish(message, self.channel, 'cega', queue)

    def run(self, from_queue, to_routing):
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

        from_channel = self.amqp_connection.channel()
        from_channel.basic_qos(prefetch_count=1)  # One job per worker
        to_channel = self.amqp_connection.channel()

        def process_request(channel, method_frame, props, body):
            correlation_id = props.correlation_id
            message_id = method_frame.delivery_tag
            LOG.debug(f'Consuming message {message_id} (Correlation ID: {correlation_id})')

            # Process message in JSON format
            answer = self.worker(json.loads(body))  # Exceptions should be already caught

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
            self.amqp_connection.close() # TODO Maybe this should be in a destructor
