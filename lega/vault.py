#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Listener moving files to the Vault
#
####################################

It simply consumes message from the message queue configured in the [vault] section.

It defaults to the `completed` queue.

When a message is consumed, it must be of the form:
* filepath
* user_id

This service should probably also implement a stort of StableID generator,
and input that in the database.
'''

import sys
import logging
import json
from pathlib import Path
import shutil
import os
import select
import pika

from .conf import CONF
from . import db
from . import amqp as broker

LOG = logging.getLogger('vault')

def work(msg, staging_pattern):
    '''Procedure to handle a message'''

    data = json.loads(msg)
    LOG.debug(data)

    file_id       = data['file_id']
    user_id       = data['user_id']
    filepath      = Path(data['filepath'])
 
    vault_area = Path( CONF.get('vault','location') )
    name = data['target_name']
    name_bits = [name[i:i+3] for i in range(0, len(name), 3)]
    LOG.debug(f'Name bits: {name_bits!r}')
    target = vault_area.joinpath(*name_bits)
    LOG.debug(f'Target: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    LOG.debug('Target parent: {}'.format(target.parent))
    starget = str(target)
    shutil.move(str(filepath), starget)
    
    # Mark it as processed in DB
    db.finalize_file(file_id, starget, target.stat().st_size)

    # remove parent folder if empty
    try:
        os.rmdir(str(filepath.parent)) # raise exception is not empty
        LOG.debug(f'Removing {filepath.parent!s}')
    except OSError:
        pass

    # Verify that the file is properly archived

    # Send message to Central EGA
    return {
        'user_id': user_id,
        #'filename': filename,
        'vault_name': starget,
    }

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    connection = broker.get_connection('cega.broker')
    channel = connection.channel()

    params = { 
             'content_type' : 'application/json',
             'delivery_mode': 2, # make message persistent
    }

    staging_pattern = CONF.get('worker','staging',raw=True)
    try:
        with db.connect() as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute('LISTEN file_completed;')

                while True:
                    if select.select([conn],[],[],5) != ([],[],[]):
                        LOG.debug('Polling')
                        conn.poll()
                        while conn.notifies:
                            notify = conn.notifies.pop(0)
                            answer = work(notify.payload, staging_pattern)
                            
                            LOG.debug('Publishing answer to Central EGA')
                            channel.basic_publish(exchange=CONF.get('cega.broker','exchange', fallback='localega.v1'),
                                                  routing_key=CONF.get('cega.broker','routing_to', fallback='sweden.file.completed'),
                                                  body=json.dumps(answer),
                                                  properties=pika.BasicProperties(**params))

    except KeyboardInterrupt:
        pass
    finally:
        connection.close()

if __name__ == '__main__':
    main()
