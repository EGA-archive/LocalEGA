# -*- coding: utf-8 -*-
# __init__ is here so that we don't collapse in sys.path with another lega module

'''
####################################
#
# Database Connection
#
####################################
'''

import logging
from enum import Enum

LOG = logging.getLogger('db')

class Status(Enum):
    Received = 'Received'
    In_Progress = 'In progress'
    Archived = 'Archived'
    Error = 'Error'
    # Received = 1
    # In_Progress = 2
    # Archived = 3
    # Error = 4

Statements = {
    'insert_submission' : ('INSERT INTO submissions (id, user_id) '
                           'VALUES(%(submission_id)s, %(user_id)s) '
                           'ON CONFLICT (id) DO UPDATE SET created_at = DEFAULT;'),

    'insert_file'       : ('INSERT INTO files (submission_id,filename,filehash,hash_algo,status) '
                           'VALUES(%(submission_id)s,%(filename)s,%(filehash)s,%(hash_algo)s,%(status)s) '
                           'RETURNING files.id;'),

    'update_status'     : 'UPDATE files SET status = %(status)s WHERE id = %(file_id)s;',

    'set_error'         : 'UPDATE files SET status = %(status)s, error = %(error)s WHERE id = %(file_id)s;',

    'get_info'          : 'SELECT filename, status, created_at, last_modified FROM files WHERE id = %(file_id)s',

}
