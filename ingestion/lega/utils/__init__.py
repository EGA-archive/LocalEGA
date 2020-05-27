"""Utility functions.

Used internally.
"""

import logging
import os
import sys
import hashlib
import traceback
from pathlib import Path

LOG = logging.getLogger(__name__)

def redact_url(url):
    """Remove user:password from the URL."""
    protocol = url[:url.index('://')+3]
    remainder = url.split('@', 1)[-1]
    # return f'{protocol}[redacted]@{remainder}'
    return protocol + '[redacted]@' + remainder

def get_sha256(checksums):
    for checksum in (checksums or []):  # bad input: "or []"
        if isinstance(checksum, dict) and checksum.get('type','').lower() == 'sha256':
            return checksum.get('value')
    else:
        return None

def add_prefix(prefix, name):
    """Concatenate prefix and name."""
    return os.path.join(prefix, name[1:] if name.startswith('/') else name)

def name2fs(name):
    """Convert a name to a file system relative path."""
    return os.path.join(*list(name[i:i+3] for i in range(0, len(name), 3)))

def mkdirs(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def clean_message(data):

    for key in ['staged_path', 'staged_name',
                'target_size',
                'type',
                'job_id',
                'job_type',
                'header',
                'payload_checksum',
                'vault_name', 'mounted_vault_paths']:
        try:
            del data[key]
        except KeyError as ke:
            pass
    # return data

def log_trace():
    """Locate the error."""
    exc_type, _, exc_tb = sys.exc_info()
    # traceback.print_tb(exc_tb)
    g = traceback.walk_tb(exc_tb)
    try:
        #frame, lineno = next(g)  # that should be the decorator
        frame, lineno = next(g)  # that should be where is happened
    except StopIteration:
        pass  # In case the trace is too short

    # fname = os.path.split(frame.f_code.co_filename)[1]
    fname = frame.f_code.co_filename
    LOG.error('Exception: %s in %s on line: %s', exc_type, fname, lineno, exc_info=True)


def add_prefix(prefix, name):
    """Concatenate prefix and name."""
    return os.path.join(prefix, name[1:] if name.startswith('/') else name)

def name2fs(name):
    """Convert a name to a file system relative path."""
    return os.path.join(*list(name[i:i+3] for i in range(0, len(name), 3)))

