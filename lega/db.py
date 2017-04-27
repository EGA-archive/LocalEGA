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
import os
import sys
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

from .conf import CONF
from .utils import cache_var

LOG = logging.getLogger('db')

__all__ = ('EGAFile',
           'create',
           'close',
           'display',
           'entry',
           'update_entry',
           'delete',
           'add', )

STATUS = {
    0: 'Error',
    1: 'In progress',
    2: 'Idle',
    3: 'Archived',
}

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

Base = declarative_base()

# class EGAFile(Base):
#     __tablename__ = 'entries'
#     id       = Column(Integer, primary_key=True)
#     filename = Column(String)
#     filepath = Column(String)
#     filehash = Column(String)
#     hashalgo = Column(String)
#     status = Column(String)

#     def __repr__(self):
#         return f"<{self.id} | {self.filename} | {STATUS[self.status]}>"

class EGAFile(Base):
    __tablename__ = 'dev_ega_downloader.file'
    file_id = Column(Integer, primary_key=True)
    dataset_stable_id = Column(String)
    packet_stable_id = Column(String)
    file_name = Column(String)
    index_name = Column(String)
    size = Column(Integer)
    stable_id = Column(String)
    status = Column(String)

    filepath = Column(String)
    filehash = Column(String)
    hashalgo = Column(String)

    def __repr__(self):
        return f"<{self.id} | {self.filename} | {STATUS[self.status]}>"

# CREATE INDEX file_dataset_stable_id_idx ON dev_ega_downloader.file (dataset_stable_id);
# CREATE UNIQUE INDEX file_file_id_idx ON dev_ega_downloader.file (file_id);
# CREATE INDEX file_stable_id_idx ON dev_ega_downloader.file (stable_id);


def create():
    LOG.debug('Creating the database')
    Base.metadata.create_all(_engine())

def close():
    _engine().close()

def display():
    LOG.debug('Displaying the whole database')
    for f in _session().query(EGAFile):
        print(f)

def entry(e):
    return _session().query(EGAFile).filter(EGAFile.id==e).first()

def update_entry(entry,value):
    CUR = _db().cursor()
    CUR.execute('UPDATE entries SET status=? WHERE id=?', (value,entry))
    CUR.close()
    _db().commit()

def delete(entry):
    CUR = _db().cursor()
    CUR.execute("DELETE FROM entries WHERE id=?", (entry,))
    CUR.close()
    _db().commit()

def add(**kwargs):
    status = kwargs.pop('status',None)
    if not status:
        status=STATUS[1] # in progress
    f = EGAFile(**kwargs)
    _session().add(f)
    _session().commit()
    return 0

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    if '--create' in args:
        print('Create DB')
        create()

    if '--add' in args:
        print('Adding to DB')
        _session().add_all([
            EGAFile(filename = f'bla{i}',
                    filepath = f'bla{i}',
                    filehash = f'aaaaaa{i}',
                    hashAlgo = 'sha256',
                    status   = 3) for i in range(10)])
        _session().commit()

    print('Displaying to DB')
    display()

    print(entry(50))

if __name__ == '__main__':
    sys.exit( main() )
