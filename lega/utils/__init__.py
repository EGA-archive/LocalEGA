"""Utility functions.

Used internally.
"""
import logging

from .exceptions import CompanionNotFound

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

def get_companion_file(filepath, ext):
    """Return the content of a companion file (in text mode), ie the `filepath` appended with the extension `ext`.

    :return: str or None if any error occurs
    """
    assert(isinstance(ext, str)), "The companion extension must be a str"
    if ext[0] != '.':
        ext = '.' + ext
    companion = str(filepath) + ext
    try:
        with open(companion, 'rt') as f:  # text file
            return f.read()
    except Exception as e:  # Not found, not readable, ...
        LOG.debug('Companion %s for %s: %r', ext, filepath, e)
        raise CompanionNotFound(companion) from e
