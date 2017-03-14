import sqlite3
import logging
import os

from lega.conf import CONF

LOG = logging.getLogger(__name__)

SCHEMA = '''\
drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  filepath text not null,
  filehash text not null,
  hashAlgo text not null,
  status integer not null
);'''

class Database():
    DB = None
    path = None

    def __init__(self):
        pass

    def setup(self):
        LOG.debug('Database setup')
        assert CONF.conf_file, "Configuration not loaded"
        # if CONF.conf_file:
        #     _db_path = path.join(path.dirname(CONF.conf_file),CONF.get('db','database'))
        # else: # default
        #     _db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..',CONF.get('db','database'))

        self.path = os.path.join(os.path.dirname(CONF.conf_file),CONF.get('db','database'))
        self.DB = sqlite3.connect(self.path)
        #self.DB.row_factory = sqlite3.Row

    def create(self):
        CUR = self.DB.cursor()
        CUR.executescript(SCHEMA)
        CUR.close()
        self.DB.commit()

    def close(self):
        self.DB.close()

    def display(self):
        LOG.debug('Displaying the whole database')
        CUR = self.DB.cursor()
        CUR.execute('SELECT id, status, filepath, filehash FROM entries ORDER BY id ASC')
        res = CUR.fetchall()
        CUR.close()
        return [ str(x) for x in res ]

    def entry(self, entry):
        CUR = self.DB.cursor()
        CUR.execute('SELECT status, filepath, filehash FROM entries WHERE id=?', (entry,))
        res = str(CUR.fetchone())
        CUR.close()
        return res

    def update_entry(self,entry,value):
        CUR = self.DB.cursor()
        CUR.execute('UPDATE entries SET status=? WHERE id=?', (value,entry))
        CUR.close()
        self.DB.commit()

    def delete(self,entry):
        CUR = self.DB.cursor()
        CUR.execute("DELETE FROM entries WHERE id=?", (entry,))
        CUR.close()
        self.DB.commit()

    def add(self,d):
        query = 'INSERT INTO entries(filepath,filehash,hashAlgo,status) VALUES(:filepath,:filehash,:hashAlgo,"In progress")'
        CUR = self.DB.cursor()
        CUR.execute(query, d)
        res = CUR.lastrowid
        CUR.close()
        self.DB.commit()
        return res
