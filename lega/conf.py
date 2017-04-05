import sys
import configparser
import logging
from logging.config import fileConfig, dictConfig
from pathlib import Path
import yaml

_config_files = [
    Path(__file__).parent / 'defaults.ini',
    Path.home() / '.lega/conf.ini'
]

f"""lega.conf
~~~~~~~~~~~~~~~~~~~~~

This module provides a dictionary-like with configuration settings.
It also loads the logging settings when `setup` is called.

The `--log <file>` argument is used to configuration where the logs go.
Without it, there is no logging capabilities.
The <file> can be in `INI` or `YAML` format.

The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from {_config_files[0]}
* from {_config_files[1]}
* and finally from the file specified as the `--conf` argument.


See `https://github.com/NBISweden/LocalEGA` for a full documentation.
:copyright: (c) 2017, NBIS System Developers.
"""

from . import __name__ as package_name
LOG = logging.getLogger(package_name)

class Configuration(configparser.SafeConfigParser):
    conf_file = None
    log_conf = None

    def setup(self,args=None, encoding='utf-8'):
        f'''Loads the configuration files in order:
           1) {_config_files[0]}
           2) {_config_files[1]}
           3) the command line arguments following `--conf`

        When done, the logging settings are loaded
        from the file specified after the `--log` argument.

        The latter file must be either in `INI` format
        or in `YAML` format, in which case, it must end in `.yaml` or `.yml`.'''

        # Finding the --conf file
        try:
            self.conf_file = args[ args.index('--conf') + 1 ]
            _config_files.append( Path(self.conf_file) )
            LOG.info(f"Overriding configuration settings with {self.conf_file}")
        except ValueError:
            LOG.info("--conf <file> was not mentioned\n"
                     "Using the default configuration files")
        except (TypeError, AttributeError): # if args = None
            LOG.info("Using the default configuration files")
        except IndexError:
            LOG.error("Wrong use of --conf <file>")
            raise ValueError("Wrong use of --conf <file>")

        self.read(_config_files, encoding=encoding)

        # Finding the --log file
        try:
            log_conf = Path(args[ args.index('--log') + 1 ])
            if log_conf.exists():
                print('Reading the log configuration from:',log_conf)
                if log_conf.suffix in ('.yaml', '.yml'):
                    with open(log_conf, 'r') as stream:
                        dictConfig(yaml.load(stream))
                        self.log_conf = log_conf
                else: # It's an ini file
                    fileConfig(log_conf)
                    self.log_conf = log_conf

        except ValueError:
            LOG.info("--log <file> was not mentioned")
        except (TypeError, AttributeError): # if args = None
            pass # No log conf
        except IndexError:
            LOG.error("Wrong use of --log <file>")
            sys.exit(2)
        except Exception as e:
            print(repr(e))
            sys.exit(2)

    def __repr__(self):
        '''Show the configuration files'''
        res = 'Configuration files:\n\t*' + '\n\t* '.join(str(s) for s in _config_files)
        if self.log_conf:
            res += '\nLogging loaded from ' + self.log_conf
        return res

CONF = Configuration()

