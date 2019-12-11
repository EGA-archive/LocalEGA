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

# These two imports are needed to get the logging config files to work
import logging  # noqa: F401
import lega.utils.logging  # noqa: F401
from logging.config import fileConfig, dictConfig

from ..utils import get_secret

_here = Path(__file__).parent
LOG_FILE = os.getenv('LEGA_LOG', None)
CONF_FILE = os.getenv('LEGA_CONF', '/etc/ega/conf.ini')


class Configuration(configparser.ConfigParser):
    """Configuration from config_files or environment variables or config server (e.g. Spring Cloud Config)."""

    def _load_log(self):
        """Try to load `filename` as configuration file."""
        global LOG_FILE
        if not LOG_FILE:
            print('No logging supplied', file=sys.stderr)
            return

        # Try first if it is a default logger
        _logger = _here / f'loggers/{LOG_FILE}.yaml'
        if _logger.exists():
            with open(_logger, 'r') as stream:
                dictConfig(yaml.load(stream))
                LOG_FILE = _logger
                return

        # Otherwise trying it as a path
        filename = Path(LOG_FILE)

        if not filename.exists():
            print(f"The file '{filename}' does not exist", file=sys.stderr)
            return

        if filename.suffix in ('.yaml', '.yml'):
            with open(filename, 'r') as stream:
                dictConfig(yaml.load(stream))
                return

        if filename.suffix in ('.ini', '.INI'):
            with open(filename, 'r') as stream:
                fileConfig(filename)
                return
        # Otherwise, fail
        print(f"Unsupported log format for {filename}", file=sys.stderr)

    def setup(self):
        """Set up."""
        if not CONF_FILE:
            print('No configuration found', file=sys.stderr)
            print('Bailing out', file=sys.stderr)
            sys.exit(2)

        self.read([CONF_FILE], encoding='utf-8')
        self._load_log()

    def __repr__(self):
        """Show the configuration files."""
        res = f'Configuration file: {CONF_FILE}'
        if LOG_FILE:
            res += f'\nLogging settings loaded from {LOG_FILE}'
        return res

    def get_value(self, section, option, conv=str, default=None, raw=False):
        """Get a specific value for this paramater either as env variable or from config files."""
        result = os.environ.get(f'{section.upper()}_{option.upper()}', None)
        if result is not None:  # it might be empty
            return self._convert(result, conv)
        result = self.get(section, option, fallback=default, raw=raw)
        if result is None:
            return result
        return self._convert(result, conv)

    def _convert(self, value, conv):
        """Convert value properly to ``str``, ``float`` or ``int``, also consider ``bool`` type."""
        if conv == bool:
            assert value, "Can not convert an empty value"
            val = value.lower()
            if val in ('y', 'yes', 't', 'true', 'on', '1'):
                return True
            elif val in ('n', 'no', 'f', 'false', 'off', '0'):
                return False
            else:
                raise ValueError(f"Invalid truth value: {val}")
        if conv == str:
            secrets_path = os.environ.get('secrets_path', '/run/secrets/')
            if value.startswith(secrets_path):
                return get_secret(value, remove_after=True)  # removes file if found
            return value
        # else
        return conv(value)  # raise error in case we can't convert an empty value


CONF = Configuration()


def configure(func):
    """Return configuration decorator."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        CONF.setup()
        return func(*args, **kwargs)
    return wrapper
