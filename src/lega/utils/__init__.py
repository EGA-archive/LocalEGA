import sys
import os
import traceback
import json
import logging
from pathlib import Path
from base64 import b64encode, b64decode
from functools import wraps
import secrets
import string

from ..conf import CONF
from . import db
from . import exceptions

LOG = logging.getLogger('utils')

def db_log_error_on_files(func):
    '''Decorator to store the raised exception in the database'''
    @wraps(func)
    def wrapper(data):
        file_id = data['file_id'] # I should have it
        try:
            res = func(data)
            return res
        except Exception as e:
            if isinstance(e,AssertionError):
                raise e

            exc_type, exc_obj, exc_tb = sys.exc_info()
            g = traceback.walk_tb(exc_tb)
            frame, lineno = next(g) # that should be the decorator
            try:
                frame, lineno = next(g) # that should be where is happened
            except StopIteration:
                pass # In case the trace is too short

            #fname = os.path.split(frame.f_code.co_filename)[1]
            fname = frame.f_code.co_filename
            LOG.debug(f'Exception: {exc_type} in {fname} on line: {lineno}')

            db.set_error(file_id, e)
    return wrapper

def sanitize_user_id(data):
    '''Removes the elixir_id from data and adds user_id instead'''

    # Elixir id is of the following form:
    # [a-z_][a-z0-9_-]*? that ends with a fixed @elixir-europe.org

    user_id = data['elixir_id'].split('@')[0]
    del data['elixir_id']
    data['user_id'] = user_id
    return user_id
