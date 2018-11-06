"""
Utility functions used internally.
"""

import os
import logging

LOG = logging.getLogger(__name__)

def get_secret(f, mode='rt'):
    with open(f, mode) as s:
        return s.read()
    # Crash if not found
    #os.remove(f)

def sanitize_user_id(user):
    '''Removes the elixir_id from data and adds user_id instead'''

    # Elixir id is of the following form:
    # [a-z_][a-z0-9_-]*? that ends with a fixed @elixir-europe.org

    return user.split('@')[0]
