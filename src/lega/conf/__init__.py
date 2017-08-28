import sys
import configparser
import logging
from logging.config import fileConfig, dictConfig
from pathlib import Path
import yaml

_here = Path(__file__).parent
_config_files =  [ _here / 'defaults.ini' ]

_loggers =  {
    'default': _here / 'loggers/default.yaml', 
    'debug':  _here / 'loggers/debug.yaml', 
    'syslog': _here / 'loggers/syslog.yaml', 
}

f"""This module provides a dictionary-like with configuration settings.
It also loads the logging settings when `setup` is called.

The `--log <file>` argument is used to configuration where the logs go.
Without it, there is no logging capabilities.

The <file> can be a path to an `INI` or `YAML` format, or a string
representing the defaults loggers (ie default, debug or syslog)


The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from {_config_files[0]}
* from the file specified as the `--conf` argument.

The files must be either in `INI` format or in `YAML` format, in
which case, it must end in `.yaml` or `.yml`.

See `https://github.com/NBISweden/LocalEGA` for a full documentation.
:copyright: (c) 2017, NBIS System Developers.

"""

LOG = logging.getLogger('lega-conf')

class Configuration(configparser.ConfigParser):
    log_conf = None

    def _load_conf(self,args=None, encoding='utf-8'):
        '''Loads a configuration file from `args`'''

        # Finding the --conf file
        try:
            conf_file = Path(args[ args.index('--conf') + 1 ])
            if conf_file not in _config_files:
                _config_files.append( conf_file )
            LOG.info(f"Overriding configuration settings with {conf_file}")
        except ValueError:
            LOG.info("--conf <file> was not mentioned\n"
                     "Using the default configuration files")
        except (TypeError, AttributeError): # if args = None
            LOG.info("Using the default configuration files")
        except IndexError:
            LOG.error("Wrong use of --conf <file>")
            raise ValueError("Wrong use of --conf <file>")

        self.read(_config_files, encoding=encoding)

    def _load_log_file(self,filename):
        '''Tries to load `filename` as configuration file'''

        if filename in ('default', 'debug', 'syslog'):
            with open(_loggers[filename], 'r') as stream:
                dictConfig(yaml.load(stream))
                self.log_conf = filename + ' logger'
                LOG.info(f'Reading the default log configuration from: {filename}')
                return
            
        # Otherwise it's a path
        LOG.info(f'Reading the log configuration from: {filename}')

        if filename and not filename.exists():
            LOG.error(f"The file '{filename}' does not exist")
            self.log_conf = None
            return

        if filename.suffix in ('.yaml', '.yml'):
            with open(filename, 'r') as stream:
                dictConfig(yaml.load(stream))
                self.log_conf = filename
        else: # It's an ini file
            fileConfig(filename)
            self.log_conf = filename

    def _load_log_conf(self,args=None):
        # Finding the --log file
        try:
            lconf = Path(args[ args.index('--log') + 1 ])
            self._load_log_file(lconf)
        except ValueError:
            LOG.info("--log <file> was not mentioned")
            default_log_conf = self.get('DEFAULT','log_conf',fallback=None)
            if default_log_conf:
                default_log_conf = Path(default_log_conf)
                self._load_log_file(default_log_conf)
        except (TypeError, AttributeError): # if args = None
            pass # No log conf
        except IndexError:
            LOG.error("Wrong use of --log <file>")
            print("Wrong use of --log <file>", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print('Error with --log:', repr(e), file=sys.stderr)
            #sys.exit(2)

    def setup(self,args=None, encoding='utf-8'):
        self._load_conf(args,encoding)
        self._load_log_conf(args)


    def __repr__(self):
        '''Show the configuration files'''
        res = 'Configuration files:\n\t* ' + '\n\t* '.join(str(s) for s in _config_files)
        if self.log_conf:
            res += '\nLogging settings loaded from ' + str(self.log_conf)
        return res

CONF = Configuration()
