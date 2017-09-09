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

def get_data(data):
    try:
        return json.loads(b64decode(data))
    except Exception as e:
        print(repr(e))
        return None
    #return json.loads(msgpack.unpackb(data))

alphabet = string.ascii_letters + string.digits
def generate_password(length):
    return ''.join(secrets.choice(alphabet) for i in range(length))


def set_file_id(data):
    '''Adding the related file into the database
    and adding the return file id into the message'''

    data['user_id'] = data['elixir_id'].split('@')[0]
    del data['elixir_id']

    filename = data['filename']
    user_id = data['user_id']

    # Insert in database
    file_id = db.insert_file(filename, user_id) 
    assert file_id is not None, 'Ouch...database problem!'
    LOG.debug(f'Created id {file_id} for {filename}')

    data['file_id'] = file_id
    return data

def sanitize_user_id(data):
    '''Removes the @elixir-europe.org from the elixir ID.'''

    data['user_id'] = data['elixir_id'].split('@')[0]
    del data['elixir_id']

    return data
