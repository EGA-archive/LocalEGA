# -*- coding: utf-8 -*-
# __init__ is here so that we don't collapse in sys.path with another lega module

from . import conf
f"""Local EGA library
~~~~~~~~~~~~~~~~~~~~~

The lega package contains code to start a _Local EGA_.

There are 3 components: ingestion, worker, vault

It is necessary to have a gpg-agent, a message broker and a postgres
database running, prior to starting the modules.

The ingestion, worker and vault modules can be respectively started as:
* `python -m lega.ingestion --conf <file> --log <file>`
* `python -m lega.worker --conf <file> --log <file>`
* `python -m lega.vault --conf <file> --log <file>`

Several worker and vault _agents_ can be started.

The ingestion module start an asyncio web-server.

The `--log <file>` argument is used to configuration where the logs go.
Without it, there is no logging capabilities.
The <file> can be in `INI` or `YAML` format.

The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from {conf._config_files[0]}
* from {conf._config_files[1]}
* and finally from the file specified as the `--conf` argument.


See `https://github.com/NBISweden/LocalEGA` for a full documentation.
:copyright: (c) 2017, NBIS System Developers.
"""

__title__ = 'Local EGA'
__version__ = VERSION = '0.1'
__author__ = 'Frédéric Haziza'
#__license__ = 'Apache 2.0'
__copyright__ = 'Local EGA @ NBIS Sweden'

# Set default logging handler to avoid "No handler found" warnings.
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
