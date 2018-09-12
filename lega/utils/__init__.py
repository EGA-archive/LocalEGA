"""
Utility functions used internally.
"""

import logging

LOG = logging.getLogger(__name__)

def get_file_content(f, mode='rb'):
    try:
        with open(f, mode) as h:
            return h.read()
    except OSError as e:
        LOG.error(f'Error reading {f}: {e!r}')
        return None

def sanitize_user_id(user):
    '''Returns username without host part of an ID on the form name@something'''

    return user.split('@')[0]
