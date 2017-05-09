# -*- coding: utf-8 -*-

'''
####################################
#
# Database Connection
#
####################################
'''

import logging
from psycopg2 import connect as db_connect

from ..conf import CONF
from . import Status, LOG, Statements
from ..utils import cache_var

@cache_var('DB_CONNECTION')
def connect():
    '''Get the database connection (which encapsulates a database session)'''
    user     = CONF.get('db','username')
    password = CONF.get('db','password')
    database = CONF.get('db','dbname')
    host     = CONF.get('db','host')
    port     = CONF.getint('db','port')
    LOG.info(f"Initializing a connection to: {host}:{port}/{database}")
    return db_connect(user=user, password=password, database=database, host=host, port=port)

def update_status(file_id, status):
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['update_status']
            cur.execute(query, {'status': status.value, 'file_id': file_id})

            # Mark submission as completed is status = Archived for all the other files belonging to the same submission id
            
    
def set_error(file_id, error):
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['set_error']
            cur.execute(query, {'status': Status.Error.value, 'error':error, 'file_id': file_id})

def set_encryption(file_id, enc_info):
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['set_encryption']
            cur.execute(query, {'enc': enc_info, 'file_id': file_id})

def set_stable_id(file_id, stable_id):
    with connect() as conn:
        with conn.cursor() as cur:
            query = Statements['set_stable_id']
            cur.execute(query, {'stable_id': stable_id, 'file_id': file_id})
