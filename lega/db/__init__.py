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
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime

from ..conf import CONF

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

metadata = sqlalchemy.MetaData()

files = sqlalchemy.Table('files', metadata,
                         Column('id',           Integer, primary_key=True, autoincrement=True),
                         Column('submission_id', None, ForeignKey('submissions.id')),
                  	 Column('filename',     Text,    nullable=False  ),
	                 Column('filehash',     Text,    nullable=False  ),
	                 Column('hash_algo',    String,  nullable=False  ),
	                 Column('status',       String                   ),
	                 Column('error',        Text                     ),
	                 Column('stable_id',    Integer                  ),
	                 Column('reencryption', Text                     )
)

submissions = sqlalchemy.Table('submissions', metadata,
                         Column('id',           Integer, primary_key=True, autoincrement=True),
                         Column('user_id',      Integer, nullable=False  ),
                  	 Column('created_at',   DateTime(timezone=True), nullable=False ),
	                 Column('completed_at', Text,                    )
)

# Base = declarative_base()
# class EGAFile(Base):
#     __tablename__ = 'files'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     filename = Column(Text, nullable=False)
#     filehash = Column(Text, nullable=False)
#     hash_algo= Column(Text, nullable=False)
#     status   = Column(Integer)
#     error   = Column(Text)
#     stable_id = Column(Integer)
#     reencryption = Column(Text)

#     def __repr__(self):
#         return f"<{self.id} | {self.filepath} | {self.status}>"

# class EGASubmission(Base):
#     __tablename__ = 'submissions'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, nullable=False)
#     created_at = Column(Text, nullable=False)
#     completed_at = Column(Text)

#     def __repr__(self):
#         return f"<{self.id} | {self.user_id} | {self.created_at}>"
