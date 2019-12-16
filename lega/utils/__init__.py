"""Utility functions used internally."""

import os


def sanitize_user_id(user):
    """Return username without host part of an ID on the form name@something."""
    return user.split('@')[0]


def get_from_file(filepath, mode='rb', remove_after=False):
    """Return file content.

    Raises ValueError if it errors.
    """
    try:
        with open(filepath, mode) as s:
            return s.read()
        # Crash if not found, or permission denied
        if remove_after:
            os.remove(filepath)
    except:
        raise ValueError(f'Error loading {filepath}')

def get_from_env(name):
    result = os.getenv(name, None)
    if result is None:
        raise ValueError(f'Environment variable {name} not found')
    return result


def redact_url(url):
    """Remove user:password from the URL."""
    return '{}[redacted]@{}'.format(url[:url.index('://')+3], url.split('@',1)[-1])
