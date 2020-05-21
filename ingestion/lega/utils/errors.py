# -*- coding: utf-8 -*-
"""Capture Errors as a decorator and logs them in the database."""

import sys
import logging
from functools import wraps
import traceback

from .db import set_error
from .exceptions import FromUser
from .amqp import publish

LOG = logging.getLogger(__name__)


######################################
#         Capture Errors             #
######################################


def log_trace():
    """Locate the error."""
    exc_type, _, exc_tb = sys.exc_info()
    # traceback.print_tb(exc_tb)
    g = traceback.walk_tb(exc_tb)
    try:
        frame, lineno = next(g)  # that should be the decorator
        frame, lineno = next(g)  # that should be where is happened
    except StopIteration:
        pass  # In case the trace is too short

    # fname = os.path.split(frame.f_code.co_filename)[1]
    fname = frame.f_code.co_filename
    LOG.error('Exception: %s in %s on line: %s', exc_type, fname, lineno, exc_info=True)


def handle_error(e, data):
    """Log error in the database.

    If error is from user send to CEGA.
    """
    # Re-raise in case of AssertionError
    if isinstance(e, AssertionError):
        raise e

    # Is it from the user?
    from_user = isinstance(e, FromUser) or isinstance(e, ValueError)

    cause = e.__cause__ or e
    LOG.error('%r', cause)  # repr(cause) = Technical

    # Locate the error
    log_trace()

    file_id = data.get('file_id', None)  # should be there
    if file_id:
        set_error(file_id, cause, from_user)
    LOG.debug('Catching error on file id: %s', file_id)
    if from_user:  # Send to CentralEGA
        org_msg = data.pop('org_msg', None)  # should be there
        org_msg['reason'] = str(cause)  # str = Informal
        LOG.info('Sending user error to local broker: %s', org_msg)
        publish(org_msg, 'cega', 'files.error')  # will fetch itself the correlation_id

        # publish(answer, to_channel, 'lega', to_routing, correlation_id=correlation_id)
        # def publish(message, channel, exchange, routing, correlation_id=None):


def catch(ret_on_error=None):
    """Return decorator to store the raised exception in the database."""
    def catch_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                data = args[-1]  # data is the last argument

                handle_error(e, data)
                # Note: let it fail and bail out if handle_error raises an exception itself

                # Should we also revert back the ownership of the file?

            return ret_on_error
        return wrapper
    return catch_error
