# -*- coding: utf-8 -*-

import os
import logging
from contextlib import contextmanager
import shutil
from pathlib import Path

from ..conf import CONF

LOG = logging.getLogger(__name__)

class FileStorage():
    def __init__(self):
        self.vault_area = Path(CONF.get('vault','location'))

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


# class S3FileReader(object):
#     """
#     Open S3 key as a file. Data is only loaded and cached on demand.

#     Parameters
#     ----------
#     s3 : S3FileSystem
#         boto3 connection
#     path : string
#         S3 bucket/key to access
#     mode : str
#         One of 'rb', 'wb', 'ab'. These have the same meaning
#         as they do for the built-in `open` function.
#     """

#     def __init__(self, storage, path, mode='rb', blocksize = 1<<22): # 1<<22 = 4194304 = 4MB
#         # self.mode = mode
#         # if mode not in {'rb', 'wb', 'ab'}:
#         #     raise NotImplementedError(f"File mode must be {{'rb', 'wb', 'ab'}}, not {mode}")
#         self.path = path
#         self.s3 = storage.s3
#         self.loc = 0
#         self.start = None
#         self.end = None
#         self.closed = False
#         self.trim = True
#         self.mpu = None
#         self.buffer = io.BytesIO()
#         self.size = s3.info(path)['Size']
#         self.blocksize = blocksize
#         # If file is less than 5MB, read it all in the buffer

#         # self.size = s3.info(path)['Size']
#         # if self.size < blocksize:
#         #     # existing file too small for multi-upload: download
#         #     self.write(s3.cat(path))

#     def tell(self):
#         return self.loc

#     def seek(self, loc, whence=0):
#         if whence == 0:
#             nloc = loc
#         elif whence == 1:
#             nloc = self.loc + loc
#         elif whence == 2:
#             nloc = self.size + loc
#         else:
#             raise ValueError("invalid whence (%s, should be 0, 1 or 2)" % whence)
#         if nloc < 0:
#             raise ValueError('Seek before start of file')
#         self.loc = nloc
#         return self.loc

#     def readline(self, length=-1):
#         """
#         Read and return a line from the stream.

#         If length is specified, at most size bytes will be read.
#         """
#         self._fetch(self.loc, self.loc + 1)
#         while True:
#             found = self.cache[self.loc - self.start:].find(b'\n') + 1
#             if 0 < length < found:
#                 return self.read(length)
#             if found:
#                 return self.read(found)
#             if self.end > self.size:
#                 return self.read(length)
#             self._fetch(self.start, self.end + self.blocksize)

#     def __next__(self):
#         out = self.readline()
#         if not out:
#             raise StopIteration
#         return out

#     next = __next__

#     def __iter__(self):
#         return self

#     def readlines(self):
#         """ Return all lines in a file as a list """
#         return list(self)

#     def _fetch(self, start, end):
#         if self.start is None and self.end is None:
#             # First read
#             self.start = start
#             self.end = end + self.blocksize
#             self.cache = _fetch_range(self.s3.s3, self.bucket, self.key,
#                                       version_id, start, self.end,
#                                       req_kw=self.s3.req_kw)
#         if start < self.start:
#             if not self.fill_cache and end + self.blocksize < self.start:
#                 self.start, self.end = None, None
#                 return self._fetch(start, end)
#             new = _fetch_range(self.s3.s3, self.bucket, self.key, version_id,
#                                start, self.start, req_kw=self.s3.req_kw)
#             self.start = start
#             self.cache = new + self.cache
#         if end > self.end:
#             if self.end > self.size:
#                 return
#             if not self.fill_cache and start > self.end:
#                 self.start, self.end = None, None
#                 return self._fetch(start, end)
#             new = _fetch_range(self.s3.s3, self.bucket, self.key, version_id,
#                                self.end, end + self.blocksize,
#                                req_kw=self.s3.req_kw)
#             self.end = end + self.blocksize
#             self.cache = self.cache + new

#     def read(self, length=-1):
#         """
#         Return data from cache, or fetch pieces as necessary

#         Parameters
#         ----------
#         length : int (-1)
#             Number of bytes to read; if <0, all remaining bytes.
#         """
#         if length < 0:
#             length = self.size
#         if self.closed:
#             raise ValueError('I/O operation on closed file.')
#         self._fetch(self.loc, self.loc + length)
#         out = self.cache[self.loc - self.start:
#                          self.loc - self.start + length]
#         self.loc += len(out)
#         if self.trim:
#             num = (self.loc - self.start) // self.blocksize - 1
#             if num > 0:
#                 self.start += self.blocksize * num
#                 self.cache = self.cache[self.blocksize * num:]
#         return out

#     def close(self):
#         if self.closed:
#             return
#         self.cache = None
#         self.closed = True

#     def __del__(self):
#         self.close()

#     def __str__(self):
#         return f"<S3FileReader {self.path}>"

#     __repr__ = __str__

#     def __enter__(self):
#         return self

#     def __exit__(self, *args):
#         self.close()

#     # Implementations of BufferedIOBase stub methods

#     def read1(self, length=-1):
#         return self.read(length)

#     def detach(self):
#         raise io.UnsupportedOperation()

#     def readinto(self, b):
#         data = self.read()
#         datalen = len(data)
#         b[:datalen] = data
#         return datalen

#     def readinto1(self, b):
#         return self.readinto(b)


# def _fetch_range(client, bucket, key, start, end, max_attempts=10):
#     LOG.debug("Fetch: %s/%s, %s-%s", bucket, key, start, end)
#     for i in range(max_attempts):
#         try:
#             resp = client.get_object(Bucket=bucket, Key=key, Range='bytes=%i-%i' % (start, end - 1))
#             return resp['Body'].read()
#         except S3_RETRYABLE_ERRORS as e:
#             LOG.debug('Exception %e on S3 download, retrying', e, exc_info=True)
#             continue
#         except ClientError as e:
#             if e.response['Error'].get('Code', 'Unknown') in ('416', 'InvalidRange'):
#                 return b''
#             else:
#                 raise
#         except Exception as e:
#             if 'time' in str(e).lower():  # Actual exception type changes often
#                 continue
#             else:
#                 raise
#     raise RuntimeError("Max number of S3 retries exceeded")

# class S3Storage():
#     def __init__(self):
#         import boto3
#         endpoint = CONF.get('vault','url')
#         region = CONF.get('vault','region')
#         bucket = CONF.get('vault','bucket', fallback='lega')
#         # access_key = CONF.get('vault','access_key')
#         # secret_key = CONF.get('vault','secret_key')
#         access_key = os.environ['S3_ACCESS_KEY']
#         secret_key = os.environ['S3_SECRET_KEY']
#         self.s3 = boto3.client('s3',
#                                endpoint_url=endpoint,
#                                region_name=region,
#                                use_ssl=False,
#                                verify=False,
#                                aws_access_key_id = access_key,
#                                aws_secret_access_key = secret_key)
#         #LOG.debug(f'S3 client: {self.s3!r}')
#         try:
#             LOG.debug('Creating "%s" bucket', bucket)
#             self.bucket = self.s3.Bucket(bucket)
#             self.bucket.create()
#         except self.s3.exceptions.BucketAlreadyOwnedByYou as e:
#             LOG.debug(f'Ignoring ({type(e)}): {e}')
#         # No need to close anymore?

#     def location(self, file_id):
#         return str(file_id)

#     def copy(self, fileobj, location):
#         self.bucket.upload_fileobj(fileobj, location)
#         return 0 # todo: return size

#     @contextmanager
#     def open(self, path, mode = 'rb'):
#         if mode != 'rb':
#             raise NotImplementedError("Mode not supported")
#         f = S3FileReader(self, path, mode=mode)
#         yield f
#         f.close()
    
