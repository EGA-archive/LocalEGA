#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import stat
from pathlib import Path

from fuse import FUSE, FuseOSError, Operations

from .conf import CONF
from .utils.amqp import file_landed

LOG = logging.getLogger('inbox')

ATTRIBUTES = ('st_uid', 'st_gid', 'st_mode', 'st_size',
              'st_nlink', 'st_atime', 'st_ctime', 'st_mtime')

class LegaFS(Operations):
    def __init__(self, root):
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
            file_landed(path)
            self.pending.remove(path)
        return os.close(fh)

    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, fdatasync, fh):
        return os.fsync(fh)


def main(args=None):

    if not args:
        import sys
        args = sys.argv[1:]

    CONF.setup(args) # re-conf, just for the logger!

    assert len(args) >= 3, "Usage: $0 <mountpoint> -o options"

    mountpoint = args[0]
    rootdir = None
    mode = 0o0

    # Creating the mountpoint if not existing.
    if not os.path.exists(mountpoint):
        LOG.debug('Mountpoint missing. Creating it')
        os.makedirs(mountpoint, exist_ok=True)

    # Collecting the mount options (last argument)
    # Fetch foreground, rootmode, setgid and rootdir from there too.
    options = { 'nothreads': True } # Enforcing nothreads
    for opt in args[-1].split(','):
        try:
            k,v = opt.split('=')
        except ValueError:
            k,v = opt, True

        if k == 'rootdir':
            rootdir = v
            continue

        if k == 'setgid':
            mode |= stat.S_ISGID
            continue

        if k == 'rootmode':
            mode |= int(v,8) # octal
            continue

        # Otherwise, add to options
        options[k] = v
 
    assert rootdir is not None, "You must specify rootdir in the mount options"

    LOG.debug(f'Mountpoint: {mountpoint} | Root dir: {rootdir}')
    if options:
        LOG.debug(f'Adding mount options: {options!r}')

    # Update the mountpoint
    if 'gid' in options:
        LOG.debug(f"Setting owner to {options['gid']}")
        os.chown(mountpoint, -1, int(options['gid'])) # user: root | grp: ega

    if mode:
        LOG.debug(f'chmod 0o{mode:o} {mountpoint}')
        os.chmod(mountpoint, mode)

    # ....aaand cue music!
    FUSE(LegaFS(rootdir), mountpoint, **options)


if __name__ == '__main__':
    main()
