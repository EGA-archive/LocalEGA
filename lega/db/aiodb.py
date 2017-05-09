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

from . import Status, LOG

async def create_engine(loop, **kwargs):
    return await _create_engine(**kwargs,loop=loop, echo=True)



async def insert_submission(engine, submission_id, user_id):
    async with engine.acquire() as conn:
        query = f'EXECUTE insert_submission({submission_id}, {user_id});'
        await conn.execute(query, echo=True)


async def insert_file(engine,
                      filename,
                      filehash,
                      hash_algo,
                      submission_id):
    async with engine.acquire() as conn:
        query = f"EXECUTE insert_file({submission_id},'{filename}','{filehash}','{hash_algo}','{Status.Received.value}');"
        LOG.debug(query)
        return await conn.scalar(query, echo=True)

async def update_status(engine, file_id, status):
    async with engine.acquire() as conn:
        query = f'EXECUTE update_status({file_id},"{status.value}");'
        await conn.execute(query, echo=True)

async def get_info(engine, file_id):
    async with engine.acquire() as conn:
        query = f'SELECT filename, status, created_at, last_modified FROM files WHERE id = {file_id}'
        res = await conn.execute(query, echo=True)
        return (res['filename'], res['status'], res['created_at'], res['last_modified'])

async def set_error(engine, file_id, error):
    async with engine.acquire() as conn:
        query = f'EXECUTE set_error({file_id},"{status.value}","{error}");'
        await conn.execute(query, echo=True)

    


