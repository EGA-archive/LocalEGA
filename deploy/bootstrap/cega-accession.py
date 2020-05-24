#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

from lega.conf import CONF
from lega.utils.amqp import consume, publish


CONN = sqlite3.connect(':memory:') # don't bother, keep it in RAM. Too bad if we restart

def init_db():
    c = CONN.cursor()
    c.execute('''CREATE TABLE accessions (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                          md5 text UNIQUE,
                                          username text,
                                          filepath text)''')
    CONN.commit()

def get_accession_id(md5, username, filepath):
    c = CONN.cursor()
    c.execute('''INSERT INTO accessions (md5,username,filepath)
                 VALUES(?,?,?)
                 ON CONFLICT(md5) DO NOTHING;''', [md5, username, filepath])
    accession_id = c.lastrowid
    CONN.commit()
    return accession_id

def work(data):
    """Read a message, split the header and decrypt the remainder."""


    decrypted_checksums = data['decrypted_checksums']

    md5_checksum = None
    for c in decrypted_checksums:
        if c.get('type') == 'md5':
            md5_checksum = c.get('value')
            break

    if md5_checksum is None:
        data['reason'] = 'Missing md5 checksum'
        publish(data, exchange='localega.v1', routing_key='files.error')
        

    filepath = data['filepath']
    username = data['user']
    accession_id = get_accession_id(md5_checksum, username, filepath)
    accession = f"EGAF{accession_id:0>11}" # I think EBI decided to use 11 digits
    print('Using accession id:', accession) # no LOG.debug for __main__ and don't care

    data['type'] = 'accession'
    data['accession_id'] = accession
    
    # Publish the answer
    publish(data, exchange='localega.v1', routing_key='accession')
    # All good: Ack message

def main():
    init_db()
    consume(work)
    
if __name__ == '__main__':
    main()
