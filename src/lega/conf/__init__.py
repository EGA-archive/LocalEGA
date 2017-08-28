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

class Configuration(configparser.ConfigParser):
    log_conf = None

    def _load_conf(self,args=None, encoding='utf-8'):
        '''Loads a configuration file from `args`'''

        # Finding the --conf file
        try:
            conf_file = Path(args[ args.index('--conf') + 1 ])
            if conf_file not in _config_files:
                _config_files.append( conf_file )
            print(f"Overriding configuration settings with {conf_file}", file=sys.stderr)
        except ValueError:
            print("--conf <file> was not mentioned\n"
                  "Using the default configuration files", file=sys.stderr)
        except (TypeError, AttributeError): # if args = None
            print("Using the default configuration files",file=sys.stderr)
        except IndexError:
            print("Wrong use of --conf <file>",file=sys.stderr)
            raise ValueError("Wrong use of --conf <file>")

        self.read(_config_files, encoding=encoding)

    def _load_log_file(self,filename):
        '''Tries to load `filename` as configuration file'''
        assert( isinstance(filename,str) )

        if not filename:
            print('No logging supplied', file=sys.stderr)
            self.log_conf = None
            return

        # Try first a default logger
        if filename in _loggers: # keys
            _logger = _loggers[filename]
            with open(_logger, 'r') as stream:
                print(f'Reading the default log configuration from: {_logger}', file=sys.stderr)
                dictConfig(yaml.load(stream))
                self.log_conf = _logger
                return

        # Otherwise trying it as a path
        filename = Path(filename)
        print(f'Reading the log configuration from: {filename}', file=sys.stderr)

        if not filename.exists():
            print(f"The file '{filename}' does not exist", file=sys.stderr)
            self.log_conf = None
            return

        if filename.suffix in ('.yaml', '.yml'):
            with open(filename, 'r') as stream:
                print(f"Loading YAML log configuration", file=sys.stderr)
                dictConfig(yaml.load(stream))
                self.log_conf = filename
                return

        if filename.suffix in ('.ini', '.INI'):
            with open(filename, 'r') as stream:
                print(f"Loading INI log configuration", file=sys.stderr)
                fileConfig(filename)
                self.log_conf = filename
                return

        print(f"Unsupported log format", file=sys.stderr)
        self.log_conf = None
            

    def _load_log_conf(self,args=None):
        # Finding the --log file
        try:
            lconf = args[ args.index('--log') + 1 ]
            print("--log argument:",lconf,file=sys.stderr)
            self._load_log_file(lconf)
        except ValueError:
            print("--log <file> was not mentioned",file=sys.stderr)
            self._load_log_file( self.get('DEFAULT','log_conf',fallback=None) )
        except (TypeError, AttributeError): # if args = None
            pass # No log conf
        except IndexError:
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
