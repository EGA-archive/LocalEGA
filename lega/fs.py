#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import errno
import logging
import stat

from fuse import FUSE, FuseOSError, Operations

from .conf import CONF
from .utils.amqp import file_landed

LOG = logging.getLogger('inbox')


class LegaFS(Operations):
    def __init__(self, root):
        self.root = root
        self.pending = set()


    # Helpers
    # =======
    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        #LOG.debug(f'Reading directory {path}')
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def rmdir(self, path):
        #LOG.debug(f"rmdir {path}")
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        #LOG.debug(f"mkdir {path}")
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        #LOG.debug(f"Running stats for {path}")
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        #LOG.debug(f"Unlink {path}")
        return os.unlink(self._full_path(path))

    def rename(self, old, new):
        #LOG.debug(f"Rename {old} into {new}")
        return os.rename(self._full_path(old), self._full_path(new))


    # File methods
    # ============

    def open(self, path, flags):
        #LOG.debug(f"Open {path}")
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        LOG.debug(f"Creating {path}")
        self.pending.add(path)
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        #LOG.debug(f"Read {path}")
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        #LOG.debug(f"Write {path}")
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        LOG.debug(f"Truncate {path}")
        self.pending.add(path)
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        #LOG.debug(f"Flush {path}")
        return os.fsync(fh)

    def release(self, path, fh):
        #LOG.debug(f"Releasing {path}")
        if path in self.pending:
            LOG.debug(f"File {path} just landed")
            file_landed(path)
            self.pending.remove(path)
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        #LOG.debug(f"fsync {path}")
        return self.flush(path, fh)


def main(args=None):

    if not args:
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
    # Especially interested in gid and allow_other. Not in uid!
    # Fetch foreground, nothreads and rootdir from there too.
    # Enforcing nothreads
    options = { 'nothreads': True }
    for opt in args[-1].split(','):
        try:
            k,v = opt.split('=')
        except ValueError:
            k,v = opt, True

        if k == 'rootdir':
            rootdir = v
            continue

        if k == 'uid': # Nope!
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
