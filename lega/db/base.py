#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Database Connection
#
####################################
'''

import logging
import sqlalchemy
from .conf import CONF

LOG = logging.getLogger('db')

@cache_var('DB_ENGINE')
def _engine():
    '''Get the database connection'''
    location = CONF.get('db','uri')
    LOG.debug(f"Connecting to DB") # Don't show location in logs
    return sqlalchemy.create_engine(location)

@cache_var('DB_SESSION')
def _session():
    '''Get the SQLAlchemy session'''
    return sqlalchemy.orm.sessionmaker(bind=_engine())()

    


