import sys
import logging
import traceback

from functools import partial, wraps
from ..utils import db
from .amqp import publish, AMQPConnectionFactory
from .exceptions import FromUser

LOG = logging.getLogger(__name__)

class Worker(object):
    conf = None
    db   = None
    _channel = None # TODO remove this in future

    def __init__(self, db):
        self.db = db

    def worker(self, *args, **kwargs):
        # TODO Do error logging in THIS function instead of wrapping it like this
        func = self.catch_error(db.crypt4gh_to_user_errors(self.do_work))
        return partial(func, *args, **kwargs)

    def catch_error(self, func):  # noqa: C901
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
