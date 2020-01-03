"""Utility functions used internally."""

import os
import logging

LOG = logging.getLogger(__name__)

def sanitize_user_id(user):
    """Return username without host part of an ID on the form name@something."""
    return user.split('@')[0]

def remove_file(filepath):
    try:
        os.remove(filepath)
    except: # Crash if not found, or permission denied
        # LOG.warning('Could not remove %s', filepath, extra={ 'correlation_id': '******' })
        LOG.warning('Could not remove %s', filepath)

def get_from_file(filepath, mode='rb', remove_after=False):
    """Return file content.

    Raises ValueError if it errors.
    """
    try:
        with open(filepath, mode) as s:
            return s.read()
    except: # Crash if not found, or permission denied
        raise ValueError(f'Error loading {filepath}')
    finally:
        if remove_after:
            remove_file(filepath)

def get_from_env(name):
    result = os.getenv(name, None)
    if result is None:
        raise ValueError(f'Environment variable {name} not found')
    return result


def redact_url(url):
    """Remove user:password from the URL."""
    return '{}[redacted]@{}'.format(url[:url.index('://')+3], url.split('@',1)[-1])
