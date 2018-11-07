# -*- coding: utf-8 -*-
'''
Capture Errors as a decorator and logs them in the database
'''

import sys
import logging
from functools import wraps
import traceback

from .db import set_error
from .exceptions import FromUser
from .amqp import publish

LOG = logging.getLogger(__name__)

######################################
##         Capture Errors           ##
######################################
def log_trace(correlation_id):
    exc_type, _, exc_tb = sys.exc_info()
    #traceback.print_tb(exc_tb)
    g = traceback.walk_tb(exc_tb)
    try:
        frame, lineno = next(g) # that should be the decorator
        frame, lineno = next(g) # that should be where is happened
    except StopIteration:
        pass # In case the trace is too short

    #fname = os.path.split(frame.f_code.co_filename)[1]
    fname = frame.f_code.co_filename
    LOG.error('[%s] Exception: %s in %s on line: %s', correlation_id, exc_type, fname, lineno)

def handle_error(e, correlation_id, data):
    try:
        # Re-raise in case of AssertionError
        if isinstance(e,AssertionError):
            raise e

        # Is it from the user?
        from_user = isinstance(e,FromUser) or isinstance(e,ValueError)

        cause = e.__cause__ or e
        LOG.error('[%s] %r', correlation_id, cause) # repr(cause) = Technical

        # Locate the error
        log_trace(correlation_id)
        
        file_id = data.get('file_id', None) # should be there
        if file_id:
            set_error(file_id, cause, from_user)
        LOG.debug('[%s] Catching error on file id: %s', correlation_id, file_id)
        if from_user: # Send to CentralEGA
            org_msg = data.pop('org_msg', None) # should be there
            org_msg['reason'] = str(cause) # str = Informal
            LOG.info('[%s] Sending user error to local broker: %s', correlation_id, org_msg)
            publish(org_msg, 'cega', 'files.error', correlation_id=correlation_id)
    except Exception as e2:
        LOG.error('[%s] While treating "%s", we caught "%r"', correlation_id, e, e2)
        print(correlation_id, '|', repr(e), 'caused', repr(e2), file=sys.stderr)


def catch(ret_on_error=None):
    '''Decorator to store the raised exception in the database'''
    def catch_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                correlation_id = args[-2] # correlation_id is the penultimate argument
                data = args[-1]           # data           is the last        argument
                handle_error(e, correlation_id, data) 

                # Should we also revert back the ownership of the file?

            return ret_on_error
        return wrapper
    return catch_error
