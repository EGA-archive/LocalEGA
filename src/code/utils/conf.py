"""Configuration Module provides a dictionary-like with configuration settings.

It also sets up the logging.

* The ``LEGA_LOG`` environment variable is used to configure where the logs go.
  Without it, there is no logging capabilities.
  Its content can be a path to an ``INI`` or ``JSON`` format, or a string
  representing the defaults loggers (ie default, debug, syslog, ...)

* The ``LEGA_CONF`` environment variable specifies the configuration settings.
  If not specified, this modules tries to load the default location ``/etc/ega/conf.ini``
  The files must be in ``INI`` format.
"""
from .conf_logging import LEGALogger
import logging
logging.setLoggerClass(LEGALogger)

import os
import configparser
import warnings
import stat
from logging.config import fileConfig, dictConfig
from pathlib import Path
import json

from . import amqp, db, key

LOG = logging.getLogger(__name__)

def get_from_file(filepath, mode='rb', remove_after=False):
    """Return file content.

    Raises ValueError if it errors.
    """
    try:
        with open(filepath, mode) as s:
            return s.read()
    except Exception as e:  # Crash if not found, or permission denied
        raise ValueError(f'Error loading {filepath}') from e
    finally:
        if remove_after:
            try:
                os.remove(filepath)
            except Exception:  # Crash if not found, or permission denied
                LOG.warning('Could not remove %s', filepath, exc_info=True)


def convert_sensitive(value):
    """Fetch a sensitive value from different sources.

    * If `value` starts with 'env://', we strip it out and the remainder acts as the name of an environment variable to read.
    If the environment variable does not exist, we raise a ValueError exception.

    * If `value` starts with 'file://', we strip it out and the remainder acts as the filepath of a file to read (in text mode).
    If any error occurs while read the file content, we raise a ValueError exception.

    * If `value` starts with 'secret://', we strip it out and the remainder acts as the filepath of a file to read (in binary mode), and we remove it after.
    If any error occurs while read the file content, we raise a ValueError exception.

    * If `value` starts with 'value://', we strip it out and the remainder acts as the value itself.
    It is used to enforce the value, in case its content starts with env:// or file:// (eg a file:// URL).

    * Otherwise, `value` is the value content itself.
    """
    if value is None:  # Not found
        return None

    # Short-circuit in case the value starts with value:// (ie, it is enforced)
    if value.startswith('value://'):
        return value[8:]

    if value.startswith('env://'):
        envvar = value[6:]
        LOG.debug('Loading value from env var: %s', envvar)
        warnings.warn(
            "Loading sensitive data from environment variable is not recommended "
            "and might be removed in future versions."
            " Use secret:// instead",
            DeprecationWarning, stacklevel=4
        )
        envvalue = os.getenv(envvar, None)
        if envvalue is None:
            raise ValueError(f'Environment variable {envvar} not found')
        return envvalue

    if value.startswith('file://'):
        path = value[7:]
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
        path = value[9:]
        LOG.debug('Loading secret from path: %s', path)
        return get_from_file(path, mode='rb', remove_after=True)  # bytes

    # It's the value itself (even if it starts with postgres:// or amqp(s)://)
    return value


class Configuration(configparser.RawConfigParser):
    """Configuration from a config file."""

    __slots__ = ('conf_file',
                 'log_file',
                 '_mq',
                 '_db',
                 '_service_key',
                 '_master_pubkey',
                 )

    def __init__(self, conf_file):
        """Set up."""
        self.conf_file = conf_file
        self._mq = None
        self._db = None
        self._service_key = None
        self._master_pubkey = None
        # Load the configuration settings
        super().__init__(self,
                         delimiters=('=', ':'),
                         comment_prefixes=('#', ';'),
                         default_section='DEFAULT',
                         interpolation=None,
                         converters={
                             'sensitive': convert_sensitive,
                         })
        if (
                not conf_file  # has no value
                or
                not os.path.isfile(conf_file)  # does not exist
                or
                not os.access(conf_file, os.R_OK)  # is not readable
        ):
            warnings.warn("No configuration settings found", UserWarning, stacklevel=2)
        else:
            self.read([conf_file], encoding='utf-8')

        # Configure the logging system
        try:
            _log = self.get('DEFAULT', 'log') # DEFAULT section
            self.log_file = _log
            self._load_log()
            if _log != self.log_file:
                LOG.debug('Logger: %s (from %s)', _log, self.log_file)
            else:
                LOG.debug('Logger: %s', self.log_file)
        except Exception as e:
            warnings.warn(f"No logging supplied: {e!r}", UserWarning, stacklevel=3)
            if e.__cause__:
                warnings.warn(f'Cause: {e.__cause__!r}', UserWarning, stacklevel=3)

    def __repr__(self):
        """Show the configuration files."""
        res = f'Configuration file: {self.conf_file}'
        if self.log_file:
            res += f'\nLogging settings loaded from {self.log_file}'
        return res

    def _load_log(self):

        if not self.log_file:
            warnings.warn("No logging supplied", UserWarning, stacklevel=2)
            return

        _here = Path(__file__).parent

        # Try first if it is a keyword-supplied logger
        _logger = _here / f'loggers/{self.log_file}.json'
        if _logger.exists():
            with open(_logger, 'r') as stream:
                dictConfig(json.load(stream))
                self.log_file = _logger # update
                return

        # Otherwise trying it as a path
        _filename = Path(self.log_file)

        if not _filename.exists():
            raise ValueError(f"The file '{self.log_file}' does not exist")

        if _filename.suffix == '.json':
            with open(_filename, 'r') as stream:
                dictConfig(json.load(stream))
                self.log_file = str(_filename) # update
                return

        if _filename.suffix in ('.ini', '.INI'):
            fileConfig(filename)
            self.log_file = str(_filename) # update
            return

        # Otherwise, fail
        raise ValueError(f"Unsupported log format for {self.log_file}")

    @property
    def mq(self):
        if self._mq is None:
            self._mq = amqp.MQConnection(self, conf_section='broker')
        return self._mq

    @property
    def db(self):
        if self._db is None:
            self._db = db.DBConnection(self, conf_section='db')
        return self._db


    # Loading the key from its storage (be it from file, or from a remote location)
    # the key_config section in the config file should describe how
    # We don't use default values: bark if not supplied
    
    @property
    def service_key(self):
        if self._service_key is None:
            key_section = self.get('DEFAULT', 'service_key')
            LOG.debug('Loading %s', key_section)
            self._service_key = getattr(key, self.get(key_section, 'loader_class'))(self, key_section)
        return self._service_key

    @property
    def master_pubkey(self):
        if self._master_pubkey is None:
            key_section = self.get('DEFAULT', 'master_pubkey')
            LOG.debug('Loading %s', key_section)
            k = getattr(key, self.get(key_section, 'loader_class'))(self, key_section)
            self._master_pubkey = k.public()
        return self._master_pubkey
