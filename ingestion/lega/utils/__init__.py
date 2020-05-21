"""Utility functions.

Used internally.
"""

import logging
import os
import sys
import hashlib
import traceback
from functools import wraps

LOG = logging.getLogger(__name__)

def sanitize_user_id(user):
    """Return username without host part of an ID on the form name@something."""
    return user.split('@')[0]

def redact_url(url):
    """Remove user:password from the URL."""
    protocol = url[:url.index('://')+3]
    remainder = url.split('@', 1)[-1]
    # return f'{protocol}[redacted]@{remainder}'
    return protocol + '[redacted]@' + remainder

def clean_message(data):

    for key in ['staged_path', 'staged_name',
                'target_size']:
        try:
            del data[key]
        except KeyError as ke:
            pass
    # return data

def log_trace():
    """Locate the error."""
    exc_type, _, exc_tb = sys.exc_info()
    # traceback.print_tb(exc_tb)
    g = traceback.walk_tb(exc_tb)
    try:
        #frame, lineno = next(g)  # that should be the decorator
        frame, lineno = next(g)  # that should be where is happened
    except StopIteration:
        pass  # In case the trace is too short

    # fname = os.path.split(frame.f_code.co_filename)[1]
    fname = frame.f_code.co_filename
    LOG.error('Exception: %s in %s on line: %s', exc_type, fname, lineno, exc_info=True)
