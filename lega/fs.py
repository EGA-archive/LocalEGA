#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import argparse
import stat

from fuse import FUSE, FuseOSError, Operations

from lega.conf import CONF
from lega.utils.amqp import file_landed

LOG = logging.getLogger('inbox')

ATTRIBUTES = ('st_uid', 'st_gid', 'st_mode', 'st_size',
              'st_nlink', 'st_atime', 'st_ctime', 'st_mtime')

DEFAULT_OPTIONS = ('nothreads', 'allow_other', 'default_permissions', 'nodev', 'noexec', 'suid')
DEFAULT_MODE = 0o750

class LegaFS(Operations):
    def __init__(self, root, user=None):
        self.user = user
        self.root = root #.rstrip('/') # remove trailing /
        self.pending = set()

    # Helper
    def _real_path(self, path):
        return os.path.join(self.root, path.lstrip('/'))

    # Filesystem methods
    # ==================

    def getattr(self, path, fh=None):
        st = os.lstat(self._real_path(path))
        return dict((key, getattr(st, key)) for key in ATTRIBUTES)

    def readdir(self, path, fh):
        yield '.'
        yield '..'
        full_path = self._real_path(path)
        #if os.path.isdir(full_path):
        g = os.walk(full_path)
        top, dirs, files = next(g) # Just here. Don't recurse
        for name in dirs: yield name
        for name in files: yield name
        g.close() # cleaning
        
    def access(self, path, mode):
        if not os.access(self._real_path(path), mode):
            raise FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        return os.chown(self._real_path(path), uid, gid)

    def chmod(self, path, mode):
        return os.chmod(self._real_path(path), mode)

    def rmdir(self, path):
        return os.rmdir(self._real_path(path))

    def mkdir(self, path, mode):
        return os.mkdir(self._real_path(path), mode)

    def statfs(self, path):
        stv = os.statvfs(self._real_path(path))
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._real_path(path))

    def rename(self, old, new):
        return os.rename(self._real_path(old), self._real_path(new))
    
    def utimens(self, path, times=None):
        return os.utime(self._real_path(path), times)


    # File methods
    # ============

    def open(self, path, flags):
        return os.open(self._real_path(path), flags)

    def create(self, path, mode, fi=None):
        LOG.debug(f"Creating {path}")
        self.pending.add(path)
        return os.open(self._real_path(path), os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        LOG.debug(f"Truncate {path}")
        self.pending.add(path)
        with open(self._real_path(path), 'r+') as f:
            f.truncate(length)

    def release(self, path, fh):
        if path in self.pending:
            LOG.debug(f"File {path} just landed")
            file_landed(self.user, path)
            self.pending.remove(path)
        return os.close(fh)

    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, fdatasync, fh):
        return os.fsync(fh)


def parse_options():
    parser = argparse.ArgumentParser(description='LegaFS filesystem')
    parser.add_argument('mountpoint', help='mountpoint for the LegaFS filesystem')
    parser.add_argument('-o', metavar='mnt_options', help='mount flags', required=True)
    args = parser.parse_args()
    
    options = dict((opt,True) for opt in DEFAULT_OPTIONS)
    
    for opt in args.o.split(','):
        try:
            k,v = opt.split('=')
        except ValueError:
            k,v = opt, True

        options[k] = v

    options['mode'] = DEFAULT_MODE if 'mode' not in options else int(options['mode'],8)
    if 'setgid' in options:
        options['mode'] |= stat.S_ISGID
        del options['setgid']

    # For the conf and logger
    _args = []
    conf = options.pop('conf', None)
    if conf:
        _args.append('--conf')
        _args.append(conf)
    logger = options.pop('log', None)
    if logger:
        _args.append('--log')
        _args.append(logger)
    CONF.setup(_args)

    return args.mountpoint, options

def main():

    mountpoint, options = parse_options()
    uid = int(options.get('uid',0))
    gid = int(options.get('gid',0))
    mode = options.pop('mode') # should be there
    rootdir = options.pop('rootdir',None)

    LOG.debug(f'Mountpoint: {mountpoint} | Root dir: {rootdir}')
    LOG.debug(f'Adding mount options: {options!r}')

    assert rootdir, "You did not specify the rootdir in the mount options"

    user = os.path.basename(rootdir if rootdir[-1] != '/' else rootdir[:-1])

    LOG.debug(f'EGA User: {user}')

    # Creating the mountpoint if not existing.
    if not os.path.exists(mountpoint):
        LOG.debug('Mountpoint missing. Creating it')
        os.makedirs(mountpoint, exist_ok=True)

    # Update the mountpoint
    LOG.debug(f"Setting owner to {uid}:{gid}")
    os.chown(mountpoint, uid, gid)

    LOG.debug(f'chmod 0o{mode:o} {mountpoint}')
    os.chmod(mountpoint, mode)

    # ....aaand cue music!
    try:
        FUSE(LegaFS(rootdir, user), mountpoint, **options)
    except RuntimeError as e:
        if str(e) == '1': # not empty
            LOG.debug(f'Already mounted')
            sys.exit(0)
        else:
            LOG.debug(f'RuntimeError {e}')
            sys.exit(2)
            


if __name__ == '__main__':
    main()
