"""Utility functions used internally."""


def sanitize_user_id(user):
    """Return username without host part of an ID on the form name@something."""
    return user.split('@')[0]
