# -*- coding: utf-8 -*-

import sys
import os
import logging
import stat
import errno
from functools import wraps

from fuse import FUSE, FuseOSError, Operations

from ..utils.amqp import get_connection, publish
from ..utils.checksum import calculate, _DIGEST as algorithms
from ..conf import CONF

LOG = logging.getLogger(__name__)

def debugme(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Skip self
        _args = args[1:]
        LOG.debug("%s args: " + ("%s " * len(_args)), func.__name__, *_args)
        return func(*args, **kwargs)
    return wrapper

class LegaFS(Operations):
    def __init__(self, user, options, domain, rootdir, **kwargs):

        LOG.debug('Mount options: %s', options)
        self.user = user
        self.root = rootdir
        self.pending = {}
        self.domain = domain
        self.channel = None
        self.connection = None
        LOG.debug("# Landing location: %s", self.root)
        # #self.headers = {}

    # Helpers
    def _real_path(self, path):
        return os.path.join(self.root, path.lstrip('/'))

    def _send_message(self, path, fh):
        if not self.channel:
            self.connection = get_connection(self.domain)
            self.channel = self.connection.channel()

        LOG.debug("File %s just landed", path)
        real_path = self._real_path(path)
        msg = {
            'user': self.user,
            'filepath': path,
        }

        if path.endswith(tuple(algorithms.keys())):
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
        st = os.lstat(self._real_path(path))
        return dict((key, getattr(st, key)) for key in ('st_uid', 'st_gid', 'st_mode', 'st_size',
                                                        'st_nlink', 'st_atime', 'st_ctime', 'st_mtime'))

    #@debugme
    def readdir(self, path, fh):
        yield '.'
        full_path = self._real_path(path)
        if full_path:
            yield '..'
        g = os.walk(full_path)
        _, dirs, files = next(g)  # Just here. Don't recurse
        for name in dirs: yield name
        for name in files: yield name
        g.close()  # cleaning

    def access(self, path, mode):
        if not os.access(self._real_path(path), mode):
            raise FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        return os.chown(self._real_path(path), uid, gid)

    def chmod(self, path, mode):
        return os.chmod(self._real_path(path), mode)

    #@debugme
    def rmdir(self, path):
        return os.rmdir(self._real_path(path))

    #@debugme
    def mkdir(self, path, mode):
        return os.mkdir(self._real_path(path), mode)

    def statfs(self, path):
        stv = os.statvfs(self._real_path(path))
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files',
                                                         'f_flag',
                                                         'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._real_path(path))

    #@debugme
    def rename(self, old, new):
        return os.rename(self._real_path(old), self._real_path(new))

    def utimens(self, path, times=None):
        return os.utime(self._real_path(path), times)

    # File methods
    # ============

    #@debugme
    def open(self, path, flags):
        return os.open(self._real_path(path), flags)
    
    #@debugme
    def create(self, path, mode, fi=None):
        return os.open(self._real_path(path), os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    #@debugme
    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    #@debugme
    def truncate(self, path, length, fh=None):
        with open(self._real_path(path), 'r+') as f:
            f.truncate(length)

    #@debugme
    def release(self, path, fh):
        if path in self.pending: # Send message
            self._send_message(path, fh)
        # Close file last.
        return os.close(fh)

    #@debugme
    def flush(self, path, fh):
        return os.fsync(fh)

    #@debugme
    def fsync(self, path, fdatasync, fh):
        return os.fsync(fh)

    #@debugme
    def destroy(self, path):
        if self.connection:
            self.connection.close()
