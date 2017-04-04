import sys
import configparser
import logging
from logging.config import fileConfig,dictConfig
from pathlib import Path
import yaml

_config_files = [
    Path(__file__).parent / 'defaults.ini',
    Path.home() / '.lega/lega.ini'
]

LOG = logging.getLogger('conf')

class Configuration(configparser.SafeConfigParser):
    conf_file = None
    log_conf = None

    def setup(self,args=None, encoding='utf-8'):
        f'''Loads the configuration files in order:
           1) {_config_files[0]}
           2) {_config_files[1]}
           3) the command line arguments following "--conf"'''

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
            LOG.info("Wrong use of --conf <file>")
            raise ValueError("Wrong use of --conf <file>")

        self.read(_config_files, encoding=encoding)

        # Finding the --log-conf file
        try:
            log_conf = Path(args[ args.index('--log-conf') + 1 ])

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
            LOG.info("--log-conf <file> was not mentioned")
        except (TypeError, AttributeError): # if args = None
            pass # No log conf
        except IndexError:
            print("Wrong use of --log-conf <file>")
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

# def run(type, value, tb):
#    if hasattr(sys, 'ps1') or not sys.stderr.isatty():
#       # we are in interactive mode or we don't have a tty-like
#       # device, so we call the default hook
#       sys.__excepthook__(type, value, tb)
#    else:
#       import traceback, pdb
#       # we are NOT in interactive mode, print the exception...
#       traceback.print_exception(type, value, tb)
#       print
#       # ...then start the debugger in post-mortem mode.
#       pdb.pm()

# sys.excepthook = run
