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
from aiopg.sa import create_engine as _create_engine
from sqlalchemy.sql import select

from . import Status, LOG, files

async def create_engine(loop, **kwargs):
    return await _create_engine(**kwargs,loop=loop, echo=True)

async def insert_submission(engine, **kwargs):
    async with engine.acquire() as conn:
        query = 'INSERT INTO submissions (id, user_id) VALUES({submission_id}, {user_id}) ON CONFLICT (id) DO UPDATE SET created_at = DEFAULT;'.format(**kwargs)
        await conn.execute(query, echo=True)


async def insert_file(engine, **kwargs):
    status = kwargs.pop('status', None)
    if not status:
        status = Status.Received.value
    async with engine.acquire() as conn:
        query = files.insert().values(**kwargs)
        return await conn.scalar(query, echo=True)

async def update_status(engine, file_id, status):
    async with engine.acquire() as conn:
        query = f'UPDATE files SET status = {status.value} WHERE id = {file_id}'
        await conn.execute(query, echo=True)

async def get_info(engine, file_id):
    async with engine.acquire() as conn:
        query = f'SELECT filename, status, created_at, last_modified FROM files WHERE id = {file_id}'
        return await conn.execute(query, echo=True)

async def set_error(engine, file_id, error):
    async with engine.acquire() as conn:
        query = f'UPDATE files SET status = {Status.Error.value}, error = {error} WHERE id = {file_id}'
        await conn.execute(query, echo=True)

    


