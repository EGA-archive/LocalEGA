# -*- coding: utf-8 -*-

import os
import logging
import tempfile
import subprocess

import boto3

from ..conf import CONF
from . import file

LOG = logging.getLogger(__name__)

def create_bucket(endpoint, region, access_key, secret_key, bucket):
    # Boto3 will check these environment variables for credentials: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    s3 = boto3.client('s3', endpoint_url=endpoint, region_name=region, use_ssl=False, verify=False,
                      aws_access_key_id = access_key,
                      aws_secret_access_key = secret_key)
    #LOG.debug(f'S3 client: {self.s3!r}')
    try:
        s3.create_bucket(Bucket=bucket)
    except s3.exceptions.BucketAlreadyOwnedByYou as e:
        LOG.debug(f'Ignoring ({type(e)}): {e}')
    # No need to close anymore?


class LegaFS(file.LegaFS):

    def __init__(self, user, options, domain, rootdir, **kwargs):

        super().__init__(user, options, domain, rootdir, **kwargs)

        self.rootdir = rootdir
        uid = options.get('uid', None)
        gid = options.get('gid', None)

        # S3 connection
        endpoint = CONF.get('s3', 'url')
        region = CONF.get('s3', 'region')

        # access_key = CONF.get('s3','access_key')
        # secret_key = CONF.get('s3','secret_key')
        access_key = os.environ['S3_ACCESS_KEY']
        secret_key = os.environ['S3_SECRET_KEY']

        LOG.debug(f'Creating bucket {user} in {endpoint}')
        create_bucket(endpoint, region, access_key, secret_key, user)

        # Mount S3FS on that mountpoint
        with tempfile.NamedTemporaryFile(mode='w') as fp:
            fp.write(access_key)
            fp.write(':')
            fp.write(secret_key)
            os.chmod(fp.fileno(), 0o600)
            fp.seek(0)

            mode = int(CONF.get('inbox', 'mode', fallback=2750), 8)

            opts = ['nodev',
                    'noexec',
                    'suid',
                    'default_permissions',
                    f'url={endpoint}',
                    'use_path_request_style',
                    f'passwd_file={fp.name}',
                    'nonempty', # Hides files in the mounted directory
                    'complement_stat',
                    f'mp_umask={mode:o}',
                    #'_netdev', # wait to network to be up
            ]
            
            if uid is not None:
                opts.append(f'uid={uid}')
            if gid is not None:
                opts.append(f'gid={gid}')

            opts = ','.join(opts)
            cmd = f's3fs {user} {rootdir} -o {opts}'
            LOG.debug(f'Running command: {cmd}')
            p = subprocess.run(cmd.split())
            if p.returncode:
                raise ValueError(f"{cmd} returned with exit status {p.returncode}")

    def destroy(self, path):
        super().destroy(path)
        LOG.debug(f"Cleanup s3fs in {self.rootdir}")
        subprocess.run(f'umount {self.rootdir}')
        
