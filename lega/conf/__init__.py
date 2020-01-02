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
import warnings
import stat
import logging
from logging.config import fileConfig, dictConfig
from pathlib import Path
import yaml

from ..utils import get_from_file, get_from_env

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
    
    # * If `value` starts with 'file://', we strip it out and the remainder acts as the filepath of a file to read (in text mode).
    # If any error occurs while read the file content, we raise a ValueError exception.

    # * If `value` starts with 'secret://', we strip it out and the remainder acts as the filepath of a file to read (in binary mode), and we remove it after.
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
        return get_from_file(path, mode='rb', remove_after=True)  # bytes

    # It's the value itself (even if it starts with postgres:// or amqp(s)://)
    return value


class Configuration(configparser.RawConfigParser):
    """Configuration from a config file."""

    logger = None

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
        try:
            self.load_log(LOG_FILE)
        except Exception as e:
            print(f'No logging supplied: {e}', file=sys.stderr)
                
    def __repr__(self):
        """Show the configuration files."""
        res = f'Configuration file: {CONF_FILE}'
        if self.logger:
            res += f'\nLogging settings loaded from {self.logger}'
        return res

    def load_log(self, filename):
        """Try to load `filename` as configuration file for logging."""
        if not filename:
            raise ValueError('No logging supplied')

        _here = Path(__file__).parent

        # Try first if it is a default logger
        _logger = _here / f'loggers/{filename}.yaml'
        if _logger.exists():
            with open(_logger, 'r') as stream:
                dictConfig(yaml.safe_load(stream))
                return _logger

        # Otherwise trying it as a path
        _filename = Path(filename)

        if not _filename.exists():
            raise ValueError(f"The file '{filename}' does not exist")

        if _filename.suffix in ('.yaml', '.yml'):
            with open(_filename, 'r') as stream:
                dictConfig(yaml.safe_load(stream))
                return filename

        if _filename.suffix in ('.ini', '.INI'):
            fileConfig(filename)
            return filename

        # Otherwise, fail
        raise ValueError(f"Unsupported log format for {filename}")


CONF = Configuration()
