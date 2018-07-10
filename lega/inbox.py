#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
FUSE layer implementation to capture when a file is uploaded to
a LocalEGA inbox. It sends a message (including filesize and
checksum) to Central EGA.
'''

# This is helping the helpdesk on the Central EGA side.
# NOTE:
#     There are issues using the file descriptors given by fuse, so we re-open the file here in python.
#     Calculating checksums and all, might make the file systems slow.
#     Hopefully, not too slow.


import sys
import os
import logging
import argparse
import stat
import errno
from functools import wraps

from fuse import FUSE, FuseOSError, Operations

from .conf import CONF
from .utils.amqp import get_connection, publish
from .utils.checksum import calculate, supported_algorithms

LOG = logging.getLogger(__name__)

# def print_func(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         # Skip self
#         _args = args[1:]
#         LOG.debug("%s args: " + ("%s " * len(_args)), func.__name__, *_args)
#         return func(*args, **kwargs)
#     return wrapper

class LegaFS(Operations):
    def __init__(self, user, options, rootdir, **kwargs):

        LOG.debug('Mount options: %s', options)
        self.user = user
        self.root = rootdir
        self.pending = set()
        self.channel = None
        self.connection = None
        LOG.debug("# Landing location: %s", self.root)
        # #self.headers = {}

    # Helpers
    def real_path(self, path):
        return os.path.join(self.root, path.lstrip('/'))

    def send_message(self, path):
        if not self.channel:
            self.connection = get_connection('broker') # local broker
            self.channel = self.connection.channel()

        LOG.debug("File %s just landed", path)
        real_path = self.real_path(path)
        msg = { 'user': self.user, 'filepath': path }

        if path.endswith(supported_algorithms()):
            with open(real_path, 'rt', encoding='utf-8') as f:
                msg['content'] = f.read()
            publish(msg, self.channel, 'cega', 'files.inbox.checksums')
        else:
            msg['filesize'] = os.stat(real_path).st_size
            c = calculate(real_path, 'md5')
            if c:
                msg['encrypted_integrity'] = {'algorithm': 'md5', 'checksum': c}
            publish(msg, self.channel, 'cega', 'files.inbox')
        LOG.debug("Message sent: %s", msg)

    # Filesystem methods
    # ==================

    def getattr(self, path, fh=None):
        st = os.lstat(self.real_path(path))
        return dict((key, getattr(st, key)) for key in ('st_uid', 'st_gid', 'st_mode', 'st_size',
                                                        'st_nlink', 'st_atime', 'st_ctime', 'st_mtime'))

    #@print_func
    def readdir(self, path, fh):
        yield '.'
        full_path = self.real_path(path)
        if full_path:
            yield '..'
        g = os.walk(full_path)
        _, dirs, files = next(g)  # Just here. Don't recurse
        for name in dirs: yield name
        for name in files: yield name
        g.close()  # cleaning

    def access(self, path, mode):
        if not os.access(self.real_path(path), mode):
            raise FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        return os.chown(self.real_path(path), uid, gid)

    def chmod(self, path, mode):
        return os.chmod(self.real_path(path), mode)

    #@print_func
    def rmdir(self, path):
        return os.rmdir(self.real_path(path))

    #@print_func
    def mkdir(self, path, mode):
        return os.mkdir(self.real_path(path), mode)

    def statfs(self, path):
        stv = os.statvfs(self.real_path(path))
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files',
                                                         'f_flag',
                                                         'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self.real_path(path))

    #@print_func
    def rename(self, old, new):
        return os.rename(self.real_path(old), self.real_path(new))

    def utimens(self, path, times=None):
        return os.utime(self.real_path(path), times)

    # File methods
    # ============

    #@print_func
    def open(self, path, flags):
        return os.open(self.real_path(path), flags)
    
    #@print_func
    def create(self, path, mode, fi=None):
        self.pending.add(path)
        return os.open(self.real_path(path), os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    #@print_func
    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    #@print_func
    def truncate(self, path, length, fh=None):
        with open(self.real_path(path), 'r+') as f:
            f.truncate(length)
            self.pending.add(path)

    #@print_func
    def release(self, path, fh):
        if path in self.pending: # Send message
            self.send_message(path)
        # Close file last.
        return os.close(fh)

    #@print_func
    def flush(self, path, fh):
        return os.fsync(fh)

    #@print_func
    def fsync(self, path, fdatasync, fh):
        return os.fsync(fh)

    #@print_func
    def destroy(self, path):
        if self.connection:
            self.connection.close()



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

    rootdir = CONF.get_value('inbox', 'location', raw=True) % user
    mode = int(CONF.get_value('inbox', 'mode'), 8)
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

    # ....aaand cue music!
    try:
        if foreground:
            options['foreground'] = True
        FUSE(LegaFS(user, options, rootdir), mountpoint, **options) # options might get updated
    except RuntimeError as e:
        if str(e) == '1':  # not empty
            LOG.debug(f'Already mounted')
            sys.exit(0)
        else:
            LOG.error(f'RuntimeError {e}')
            sys.exit(2)


if __name__ == '__main__':
    main()
