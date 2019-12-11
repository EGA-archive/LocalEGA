"""Utility functions used internally."""

import os


def sanitize_user_id(user):
    """Return username without host part of an ID on the form name@something."""
    return user.split('@')[0]


def get_secret(f, mode='rb', remove_after=False):
    """Return secret."""
    with open(f, mode) as s:
        return s.read()
    # Crash if not found, or permission denied
    if remove_after:
        os.remove(f)
