# -*- coding: utf-8 -*-

import io

class IOBuf(object):
    """\
    This module implements a subset of the io interface, 
    and does not buffer in memory data that have been read/consumed.

    Internally, we use a `bytes`-object and slice it to update it.
    """

    def __init__(self):
        self._buf = b''
        self._bufsize = 0

    def read(self, size=None):
        '''Returns the whole buffer when size is None.
        If size is not None, it returns whatever it can from the buffer.'''
        if size is None or self._bufsize < size:
            size = self._bufsize

        data = self._buf[:size]
        self._bufsize -= size
        self._buf = self._buf[size:]
        return data

    def readinto(self, b): # called by the read_{2,4} functions
        size = len(b)
        data = self.read(size)
        assert( data )
        b[:] = data
        return size

    def tell(self): # It gets called but in context where
        return None # the return value doesn't bare a meaning

    def write(self, data):
        '''Appends data to the buffer'''
        data_length = len(data)
        self._buf += data
        self._bufsize += data_length

    def get_size(self):
        return self._bufsize
