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
    _channel = None # TODO remove this in future

    def __init__(self, db, amqp_connection):
        assert db is not None, "Database connection is needed"
        assert amqp_connection is not None, "AMQP Connection is needed"
        self.db = db
        self.amqp_connection = amqp_connection

    def worker(self, *args, **kwargs):
        # TODO Do error logging in THIS function instead of wrapping it like this
        func = self._catch_error(db.crypt4gh_to_user_errors(self.do_work))
        return partial(func, *args, **kwargs)

    def _catch_error(self, func):  # noqa: C901
        """Store the raised exception in the database decorator."""
        @wraps(func)
        def wrapper(*args):
            try:
                return func(*args)
            except Exception as e:
                if isinstance(e, AssertionError):
                    raise e

                exc_type, _, exc_tb = sys.exc_info()
                g = traceback.walk_tb(exc_tb)
                frame, lineno = next(g)  # that should be the decorator
                try:
                    frame, lineno = next(g)  # that should be where is happened
                except StopIteration:
                    pass  # In case the trace is too short

                fname = frame.f_code.co_filename
                LOG.error(f'Exception: {exc_type} in {fname} on line: {lineno}')
                from_user = isinstance(e, FromUser)
                cause = e.__cause__ or e
                LOG.error(f'{cause!r} (from user: {from_user})')  # repr = Technical

                try:
                    data = args[-1]  # data is the last argument
                    file_id = data.get('file_id', None)  # should be there
                    if file_id:
                        self.db.set_error(file_id, cause, from_user)
                    LOG.debug('Catching error on file id: %s', file_id)
                    if from_user:  # Send to CentralEGA
                        org_msg = data.pop('org_msg', None)  # should be there
                        org_msg['reason'] = str(cause)  # str = Informal
                        LOG.info(f'Sending user error to local broker: {org_msg}')
                        if self._channel is None:
                            # TODO this function knows too much
                            amqp_cf = AMQPConnectionFactory(self.conf)
                            self._channel = amqp_cf.get_connection('broker').channel()
                        publish(org_msg, _channel, 'cega', 'files.error')
                except Exception as e2:
                    LOG.error(f'While treating "{e}", we caught "{e2!r}"')
                    print(repr(e), 'caused', repr(e2), file=sys.stderr)
                return None
        return wrapper

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

        worker = self.worker()

        def process_request(channel, method_frame, props, body):
            correlation_id = props.correlation_id
            message_id = method_frame.delivery_tag
            LOG.debug(f'Consuming message {message_id} (Correlation ID: {correlation_id})')

            # Process message in JSON format
            answer = worker(json.loads(body))  # Exceptions should be already caught

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
