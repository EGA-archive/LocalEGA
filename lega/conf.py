import configparser
import logging
from os.path import dirname, join expanduser


_config_files = [
    join(os.path.dirname(__file__),'defaults.ini'),
    expanduser('~/.lega.ini')
]

LOG = logging.getLogger(__name__)

class Configuration(configparser.SafeConfigParser):
    conf_file = None

    def setup(self,args=None, encoding='utf-8'):
        '''Loads the configuration files in order:
           1) {}
           2) ~/.lega.ini
           3) the command line arguments following "--conf"'''.format(_default_conf_file)

        # Finding the --conf file
        try:
            self.conf_file = args[ args.index('--conf') + 1 ]
            _config_files.append( self.conf_file )
        except ValueError:
            LOG.info("--conf <file> was not mentioned\n"
                     "Using the default configuration file: "+_default_conf_file)
        except (TypeError, AttributeError): # if args = None
            LOG.info("Using the default configuration file: "+_default_conf_file)
        except IndexError:
            LOG.info("Wrong use of --conf <file>")
            raise configparser.Error("Wrong use of --conf <file>")

        self.read(_config_files, encoding=encoding)


    def log_setup(self,logger, domain):
        # Log level
        log_level = getattr(logging, self.get(domain,'log_level',fallback='INFO').upper(), logging.INFO)
        logger.debug('[{}] Setting Log level: {}'.format(domain,logging.getLevelName(log_level)))
        logger.setLevel( log_level )

        # Log Formatting
        log_format = self.get(domain,'log_format',fallback=None,raw=True)
        if log_format:
            print('[{}] Setting Log Format to {}'.format(domain,log_format))
            formatter = logging.Formatter(fmt=log_format, style='{')
            for ch in logger.handlers:
                ch.setFormatter(formatter)

        # Output
        log = self.get(domain,'log',fallback=None)
        if log:
            print('[{}] Setting Log Output to {}'.format(domain,log))
            logger.addHandler(logging.FileHandler(log, 'a'))


CONF = Configuration()
