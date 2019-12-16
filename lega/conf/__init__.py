"""Configuration Module provides a dictionary-like with configuration settings.

It also loads the logging settings when ``setup`` is called.

* The ``LEGA_LOG`` environment variable is used to configure where the logs go.
  Without it, there is no logging capabilities.
  Its content can be a path to an ``INI`` or ``YAML`` format, or a string
  representing the defaults loggers (ie default, debug, syslog, ...)

* The ``LEGA_CONF`` environment variable specifies the configuration settings.
  If not specified, this modules tries to load the default location ``/etc/ega/conf.ini``
  The files must be either in ``INI`` format or in ``YAML`` format, in
  which case, it must end in ``.yaml`` or ``.yml``.
"""

import sys
import os
import configparser
from pathlib import Path
import yaml
from functools import wraps
import warnings
import stat

# These two imports are needed to get the logging config files to work
import logging  # noqa: F401
from logging.config import fileConfig, dictConfig

from ..utils import get_from_file, get_from_env

_here = Path(__file__).parent
LOG_FILE = os.getenv('LEGA_LOG', None)
CONF_FILE = os.getenv('LEGA_CONF', '/etc/ega/conf.ini')

LOG = logging.getLogger(__name__)


def convert_sensitive(value):
    if value is None:  # Not found
        return None

    # Short-circuit in case the value starts with value:// (ie, it is enforced)
    if value.startswith('value://'):
        return value[8:]

    # * If `value` starts with 'env://', we strip it out and the remainder acts as the name of an environment variable to read.
    # If the environment variable does not exist, we raise a ValueError exception.
    
    # * If `value` starts with 'file://', we strip it out and the remainder acts as the filepath of a file to read.
    # If any error occurs while read the file content, we raise a ValueError exception.
    
    # * If `value` starts with 'value://', we strip it out and the remainder acts as the value itself.
    # It is used to enforce the value, in case its content starts with env:// or file:// (eg a file:// URL).
    
    # * Otherwise, `value` is the value content itself. 

    if value.startswith('env://'):
        envvar = value[6:]
        LOG.debug('Loading value from env var: %s', envvar)
        warnings.warn(
            "Loading sensitive data from environment variable is not recommended "
            "and might be removed in future versions."
            " Use secret:// instead",
            DeprecationWarning, stacklevel=4
        )
        return get_from_env(envvar)

    if value.startswith('file://'):
        path=value[7:]
        LOG.debug('Loading value from path: %s', path)
        statinfo = os.stat(path)
        if statinfo.st_mode & stat.S_IRGRP or statinfo.st_mode & stat.S_IROTH:
            warnings.warn(
                "Loading sensitive data from a file that is group or world readable "
                "is not recommended and might be removed in future versions."
                " Use secret:// instead",
                DeprecationWarning, stacklevel=4
            )
        return get_from_file(path, mode='rt')  # str

    if value.startswith('secret://'):
        path=value[9:]
        LOG.debug('Loading secret from path: %s', path)
        return get_from_file(path, remove_after=True)  # binary

    # It's the value itself (even if it starts with postgres:// or amqp(s)://)
    return value


class Configuration(configparser.RawConfigParser):
    """Configuration from a config file."""
    
    def __init__(self):
        """Set up."""
        if not CONF_FILE:
            print('No configuration found', file=sys.stderr)
            print('Bailing out', file=sys.stderr)
            sys.exit(2)

        configparser.RawConfigParser.__init__(self,
                                              delimiters=('=', ':'),
                                              comment_prefixes=('#', ';'),
                                              default_section='DEFAULT',
                                              interpolation=None,
                                              converters={
                                                  'sensitive': convert_sensitive,
                                              })
        self.read([CONF_FILE], encoding='utf-8')
        self.load_log()

    def load_log(self):
        """Try to load `filename` as configuration file."""
        global LOG_FILE
        if not LOG_FILE:
            print('No logging supplied', file=sys.stderr)
            return

        # Try first if it is a default logger
        _logger = _here / f'loggers/{LOG_FILE}.yaml'
        if _logger.exists():
            with open(_logger, 'r') as stream:
                dictConfig(yaml.safe_load(stream))
                LOG_FILE = _logger
                return

        # Otherwise trying it as a path
        filename = Path(LOG_FILE)

        if not filename.exists():
            print(f"The file '{filename}' does not exist", file=sys.stderr)
            return

        if filename.suffix in ('.yaml', '.yml'):
            with open(filename, 'r') as stream:
                dictConfig(yaml.safe_load(stream))
                return

        if filename.suffix in ('.ini', '.INI'):
            with open(filename, 'r') as stream:
                fileConfig(filename)
                return
        # Otherwise, fail
        print(f"Unsupported log format for {filename}", file=sys.stderr)


    def __repr__(self):
        """Show the configuration files."""
        res = f'Configuration file: {CONF_FILE}'
        if LOG_FILE:
            res += f'\nLogging settings loaded from {LOG_FILE}'
        return res


CONF = Configuration()
