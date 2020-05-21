# -*- coding: utf-8 -*-
# __init__ is here so that we don't collapse in sys.path with another lega module

"""The lega package contains code to start a *Local EGA*."""

__title__ = 'Local EGA'
__version__ = '1.2'
__author__ = 'Frédéric Haziza'
__author_email__ = 'frederic.haziza@crg.eu'
__license__ = 'Apache License 2.0'
__copyright__ = __title__ + ' @ CRG, Barcelona'

import sys
assert sys.version_info >= (3, 7), "This tool requires python version 3.7 or higher"

# This updates the logging class from all loggers used in this package.
# The new logging class injects a correlation id to the log record.
import logging
from .conf.logging import LEGALogger
logging.setLoggerClass(LEGALogger)

# Send warnings using the package warnings to the logging system
# The warnings are logged to a logger named 'py.warnings' with a severity of WARNING.
# See: https://docs.python.org/3/library/logging.html#integration-with-the-warnings-module
import warnings
logging.captureWarnings(True)
warnings.simplefilter("default")  # do not ignore Deprecation Warnings
