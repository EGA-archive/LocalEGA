#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Async Database Access
#
####################################
'''

import logging
import aiopg

from . import Status, LOG, Statements

async def create_pool(loop, **kwargs):
    return await aiopg.create_pool(**kwargs,loop=loop, echo=True)

async def insert_submission(pool, **kwargs):
    LOG.debug(kwargs)
    with (await pool.cursor()) as cur:
        query = Statements['insert_submission']
        await cur.execute(query, kwargs)

async def insert_file(pool, **kwargs):
    if not kwargs.pop('status', None):
        kwargs['status'] = Status.Received.value
    LOG.debug(kwargs)
    with (await pool.cursor()) as cur:
        query = Statements['insert_file']
        await cur.execute(query, kwargs)
        return (await cur.fetchone())[0] # returning the id

async def update_status(pool, file_id, status):
    with (await pool.cursor()) as cur:
        query = Statements['update_status']
        await cur.execute(query, {'status': status.value, 'file_id': file_id})

async def get_info(pool, file_id):
    with (await pool.cursor()) as cur:
        query = Statements['get_info']
        await cur.execute(query, {'file_id': file_id})
        return await cur.fetchone()
    
async def set_error(pool, file_id, error):
    with (await pool.cursor()) as cur:
        query = Statements['set_error']
        await cur.execute(query, {'status': Status.Error.value, 'error':error, 'file_id': file_id})

    


