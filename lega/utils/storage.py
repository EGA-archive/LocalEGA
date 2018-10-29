# -*- coding: utf-8 -*-

'''
File I/O for disk or S3 Object storage
'''

import os
import logging
from contextlib import contextmanager
import shutil
from pathlib import Path

from ..conf import CONF
import io

LOG = logging.getLogger(__name__)


class FileStorage():
    """Vault storage on disk and related I/O."""

    def __init__(self):
        self.vault_area = Path(CONF.get_value('vault', 'location'))

    def location(self, file_id):
        name = f"{file_id:0>20}" # filling with zeros, and 20 characters wide
        name_bits = [name[i:i+3] for i in range(0, len(name), 3)]
        target = self.vault_area.joinpath(*name_bits)
        target.parent.mkdir(parents=True, exist_ok=True)
        return str(target)

    def copy(self, fileobj, location):
        with open(location, 'wb') as h:
            shutil.copyfileobj(fileobj, h)
        return os.stat(location).st_size

    @contextmanager
    def open(self, path, mode = 'rb'):
        f = open(path, mode)
        yield f
        f.close()


class S3FileReader(object):
    """
    Implements a few of the BufferedIOBase methods
    """
    def __init__(self, s3, bucket, path, mode='rb', blocksize = 1<<22): # 1<<22 = 4194304 = 4MB
        
        if mode != 'rb': # if mode not in ('rb', 'wb', 'ab'):
            raise NotImplementedError(f"File mode '{mode}' not supported")
        self.mode = mode
        self.path = path
        self.s3 = s3
        self.loc = 0
        self.start = None
        self.end = None
        self.closed = False
        self.bucket = bucket
        self.info = s3.head_object(Bucket=bucket, Key=path)
        self.size = self.info['ContentLength']
        # self.buffer = io.BytesIO() # cache
        # self.blocksize = blocksize
        # # If file is less than 5MB, read it all in the buffer
        # if self.size < blocksize:
        #     # existing file too small for multi-upload: download
        #     self.buffer.write(self.read())

    def tell(self):
        return self.loc

    def seek(self, loc, whence=0):
        if whence == 0: # from start
            nloc = loc
        elif whence == 1: # from here
            nloc = self.loc + loc
        elif whence == 2: # from end
            nloc = self.size + loc
        else:
            raise ValueError("invalid whence (%s, should be 0, 1 or 2)" % whence)
        if nloc < 0:
            raise ValueError('Seek before start of file')
        self.loc = nloc
        return self.loc

    # def readline(self, length=-1):
    #     self._fetch(self.loc, self.loc + 1)
    #     while True:
    #         found = self.cache[self.loc - self.start:].find(b'\n') + 1
    #         if 0 < length < found:
    #             return self.read(length)
    #         if found:
    #             return self.read(found)
    #         if self.end > self.size:
    #             return self.read(length)
    #         self._fetch(self.start, self.end + self.blocksize)

    # def __next__(self):
    #     out = self.readline()
    #     if not out:
    #         raise StopIteration
    #     return out

    # next = __next__

    # def __iter__(self):
    #     return self

    # def readlines(self):
    #     """ Return all lines in a file as a list """
    #     return list(self)

    def read(self, length=-1):
        if self.closed:
            raise ValueError('I/O operation on closed file.')

        if self.loc == self.size: # at the end already
            return b''

        if length < 0: # the rest of the file
            length = self.size - self.loc 

        end = min(self.loc + length, self.size) # in case it's too much
        out = self._fetch(self.loc, end)
        self.loc += len(out)
        return out

    def close(self):
        if self.closed:
            return
        self.closed = True

    def __del__(self):
        self.close()

    def __str__(self):
        return f"<S3FileReader {self.path}>"

    __repr__ = __str__

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # Implementations of BufferedIOBase stub methods

    def read1(self, length=-1):
        return self.read(length)

    def detach(self):
        raise io.UnsupportedOperation()

    def readinto(self, b):
        data = self.read()
        datalen = len(data)
        b[:datalen] = data
        return datalen

    def readinto1(self, b):
        return self.readinto(b)

    def _fetch(self, start, end, max_attempts=10):
        # if end > self.size:
        #     end = self.size
        assert end <= self.size
        #LOG.debug("Fetch: Bucket: %s, File=%s, Range: %s-%s, Chunk: %s", self.bucket, self.path, start, end, end-start)
        for i in range(max_attempts):
            try:
                resp = self.s3.get_object(Bucket=self.bucket, Key=self.path, Range='bytes=%i-%i' % (start, end - 1))
                return resp['Body'].read()
            # except socket.timeout as e:
            #     LOG.debug('Exception %e on S3 download, retrying', e, exc_info=True)
            #     continue
            # except self.s3.exceptions.ClientError as e:
            #     if e.response['Error'].get('Code', 'Unknown') in ('416', 'InvalidRange'):
            #         return b''
            #     else:
            #         raise
            except Exception as e:
                LOG.debug('Exception %e', e, exc_info=True)
                if 'time' in str(e).lower():  # Actual exception type changes often
                    continue
                raise
        raise RuntimeError("Max number of S3 retries exceeded")


class S3Storage():
    """Vault S3 object storage and related I/O."""

    def __init__(self):
        import boto3
        import socket

        endpoint = CONF.get_value('vault', 'url')
        region = CONF.get_value('vault', 'region')
        bucket = CONF.get_value('vault', 'bucket', default='lega')
        # access_key = CONF.get_value('vault', 'access_key')
        # secret_key = CONF.get_value('vault', 'secret_key')
        access_key = os.environ['S3_ACCESS_KEY']
        secret_key = os.environ['S3_SECRET_KEY']
        self.s3 = boto3.client('s3',
                               endpoint_url=endpoint,
                               region_name=region,
                               use_ssl=False,
                               verify=False,
                               aws_access_key_id = access_key,
                               aws_secret_access_key = secret_key)
        #LOG.debug(f'S3 client: {self.s3!r}')
        try:
            LOG.debug('Creating "%s" bucket', bucket)
            self.bucket = bucket
            self.s3.create_bucket(Bucket=bucket)
        except self.s3.exceptions.BucketAlreadyOwnedByYou as e:
            LOG.debug(f'Ignoring ({type(e)}): {e}')
        # No need to close anymore?

    def location(self, file_id):
        return str(file_id)

    def copy(self, fileobj, location):
        self.s3.upload_fileobj(fileobj, self.bucket, location)
        resp = self.s3.head_object(Bucket=self.bucket, Key=location)
        return resp['ContentLength']

    @contextmanager
    def open(self, path, mode = 'rb'):
        f = S3FileReader(self.s3, self.bucket, path, mode=mode)
        yield f
        f.close()
    
