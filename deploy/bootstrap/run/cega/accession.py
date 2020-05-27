#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import configparser

from docopt import docopt

__doc__ = f'''

Utility to help bootstrap a LocalEGA instance.

Usage:
   {sys.argv[0]} [options] <conf>

Options:
   -h, --help             Prints this help and exit
   -v, --version          Prints the version and exits
   -V, --verbose          Prints more output
 
'''

def main(conf, args):

    config = configparser.RawConfigParser()
    config['DEFAULT'] = {
        'queue': 'v1.files.verified',
        'exchange': conf.get('mq', 'exchange'),
        'cega_exchange': conf.get('mq', 'exchange'), 
        'cega_error_key': 'files.error',
    }

    config['broker'] = {
        'connection': conf.get('mq', 'connection'),
        'enable_ssl': 'yes',
        'verify_peer': 'yes',
        'verify_hostname': 'no',
        'cacertfile': '/cega/CA.crt',
        'certfile': '/cega/ssl.crt',
        'keyfile': '/cega/ssl.key',
    }

    # output
    config.write(sys.stdout)


if __name__ == '__main__':
    args = docopt(__doc__,
                  sys.argv[1:],
                  help=True,
                  version='CentralEGA accession service boostrap (version 0.2)')
    conf = configparser.RawConfigParser()
    conf.read(args['<conf>'])
    main(conf, args)
