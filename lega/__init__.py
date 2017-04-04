# Do not collapse in sys.path with another lega module

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = VERSION = '0.1'

__all__ = ['conf',
           'amqp',
           'checksum',
           'crypto',
           #'db',
           'ingestion',
           'utils',
           'vault',
           'worker',
]
