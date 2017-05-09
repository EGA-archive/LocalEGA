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
