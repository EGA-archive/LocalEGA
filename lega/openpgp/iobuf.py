# -*- coding: utf-8 -*-

import io

class IOBuf(object):
    """ Some description
    """

    def __init__(self):
        """ 
        """
        self._buf = b''
        self._bufsize = 0

    def read(self, size=None):
        if size is None:
            size = self._bufsize

        if self._bufsize < size:
            return None # not enough data

        data = self._buf[:size]
        self._bufsize -= size
        self._buf = self._buf[size:]
        return data

    def readinto(self, b):
        size = len(b)
        data = self.read(size)
        assert( data )
        b[:] = data
        return size

    def tell(self):
        return None

    def write(self, data):
        data_length = len(data)
        self._buf += data
        self._bufsize += data_length

    def get_size(self):
        return self._bufsize
