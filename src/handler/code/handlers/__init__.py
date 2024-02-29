import logging
import os
from pathlib import Path

LOG = logging.getLogger(__name__)

# the clean_empty defaults to False to avoid a datarace
def clean_staging(config, data, clean_empty=False):
    try:
        filepath = data['filepath']
        username = data['user']
        staging_prefix = config.get('staging', 'location', raw=True)
        staging_path = os.path.join(staging_prefix % username, filepath.strip('/') )
        LOG.info('Cleaning %s', staging_path)
        p = Path(staging_path)
        p.unlink()
    except Exception as e:
        LOG.warning('Ignoring staging file error: %r', e)

    if clean_empty:
        # Clean empty directories
        staging_topdir = Path(staging_prefix % '')
        while True:
            p = p.parent
            try:
                if p == staging_topdir:
                    break
                p.rmdir() # fail if not empty, and break the loop
                LOG.debug('Empty directory %s removed', p)
            except Exception as e2:
                break


