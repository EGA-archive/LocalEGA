#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
FUSE layer implementation to capture when a file is uploaded to
a LocalEGA inbox

It send a message (including filesize and
checksum) to Central EGA.

This is helping the helpdesk on the Central EGA side.

.. note::
    There are issues using the file descriptors given by fuse, so we re-open the file here in python.
    Calculating checksums and all, might make the file systems slow.
    Hopefully, not too slow.
'''
import sys
import os
import logging
import argparse
import stat
import errno
from importlib import import_module

from fuse import FUSE, FuseOSError, Operations

from ..conf import CONF

LOG = logging.getLogger(__name__)

def parse_options():
    parser = argparse.ArgumentParser(description='LegaFS filesystem')
    parser.add_argument('mountpoint', help='mountpoint for the LegaFS filesystem')
    parser.add_argument('-o', metavar='mnt_options', help='mount flags: comma-separated key[=val]. The "driver" key is required.', required=True)
    parser.add_argument('-f', '--foreground', help='Stay in foreground', action='store_true')
    args = parser.parse_args()

    options = {}
    for opt in args.o.split(','):
        try:
            k, v = opt.split('=')
        except ValueError:
            k, v = opt, True
        options[k] = v

    # For the conf and logger
    _args = []
    conf = options.pop('conf', None)
    if conf:
        _args.append('--conf')
        _args.append(conf)
        print('Using conf', conf)
    logger = options.pop('log', None)
    if logger:
        _args.append('--log')
        _args.append(logger)
        print('Using logger', logger)
    CONF.setup(_args)

    return args.mountpoint, args.foreground, options


def main():

    mountpoint, foreground, options = parse_options()

    user = options.pop('user', None)
    assert user, "You did not specify the user in the mount options"
    LOG.info(f'Mounting inbox for EGA User "{user}"')

    rootdir = CONF.get('inbox', 'location', raw=True) % user
    mode = int(CONF.get('inbox', 'mode'), 8)
    uid = options.get('uid', None)
    gid = options.get('gid', None)

    if not os.path.exists(mountpoint):
        LOG.debug('Mountpoint missing. Creating it')
        os.makedirs(mountpoint, exist_ok=True)

        # Changing ownership if newly created
        if uid is not None and gid is not None:
            LOG.debug('Updating ownership')
            os.chown(mountpoint, int(uid), int(gid))
        os.chmod(mountpoint, mode)

    # Create rootdir for that user
    if not os.path.exists(rootdir):
        LOG.debug('Rootdir missing. Creating it')
        os.makedirs(rootdir, exist_ok=True)

        if uid is not None and gid is not None:
            LOG.debug('Updating ownership for rootdir')
            os.chown(rootdir, int(uid), int(gid))
        os.chmod(rootdir, mode)

    # Which module to use
    driver = CONF.get('inbox', 'driver', fallback='file') # default to file
    m = import_module(f'{__name__}.{driver}')
    fs = m.LegaFS(user, options, 'broker', rootdir)

    # ....aaand cue music!
    try:
        if foreground:
            options['foreground'] = True
        FUSE(fs, mountpoint, **options)
    except RuntimeError as e:
        if str(e) == '1':  # not empty
            LOG.debug(f'Already mounted')
            sys.exit(0)
        else:
            LOG.error(f'RuntimeError {e}')
            sys.exit(2)


if __name__ == '__main__':
    main()
