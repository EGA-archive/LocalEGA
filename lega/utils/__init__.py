"""Utility functions.

Used internally.
"""


def sanitize_user_id(user):
    """Return username without host part of an ID on the form name@something."""
    return user.split('@')[0]


def redact_url(url):
    """Remove user:password from the URL."""
    protocol = url[:url.index('://')+3]
    remainder = url.split('@', 1)[-1]
    # return f'{protocol}[redacted]@{remainder}'
    return protocol + '[redacted]@' + remainder
