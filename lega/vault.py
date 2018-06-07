# -*- coding: utf-8 -*-

import logging

from .conf import CONF

LOG = logging.getLogger(__name__)

class FileStorage():
    def __init__(self):
        import os
        import shutil
        from pathlib import Path
        self.vault_area = Path(CONF.get('vault','location'))

    def location(self, file_id):
        name = f"{file_id:0>20}" # filling with zeros, and 20 characters wide
        name_bits = [name[i:i+3] for i in range(0, len(name), 3)]
        target = self.vault_area.joinpath(*name_bits)
        target.parent.mkdir(parents=True, exist_ok=True)
        return str(target)

    def copy(fileobj, location):
        with open(location, 'wb') as h:
            shutil.copyfileobj(fileobj, h)
        return os.stat(location).st_size


class S3Storage():
    def __init__(self):
        import boto3
        endpoint = CONF.get('vault','url')
        region = CONF.get('vault','region')
        self.bucket = CONF.get('vault','bucket', fallback='lega')
        # access_key = CONF.get('vault','access_key')
        # secret_key = CONF.get('vault','secret_key')
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
            LOG.debug('Creating "%s" bucket', self.bucket)
            self.s3.create_bucket(Bucket=self.bucket)
        except self.s3.exceptions.BucketAlreadyOwnedByYou as e:
            LOG.debug(f'Ignoring ({type(e)}): {e}')
        # No need to close anymore?

    def location(self, file_id):
        return str(file_id)

    def copy(fileobj, location):
        self.s3.upload_fileobj(fileobj, self.bucket, location)
        return 0 # todo: return size
