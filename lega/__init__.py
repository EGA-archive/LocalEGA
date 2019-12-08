# -*- coding: utf-8 -*-
# __init__ is here so that we don't collapse in sys.path with another lega module

"""The lega package contains code to start a *Local EGA*."""

__title__ = 'Local EGA'
__version__ = VERSION = '1.1'
__author__ = 'Frédéric Haziza'
__license__ = 'Apache 2.0'
__copyright__ = 'Local EGA @ NBIS Sweden'

# Set default logging handler to avoid "No handler found" warnings.
import logging

# This updates the logging class from all loggers used in this package.
# The new logging class injects a correlation id to the log record.
from .utils.logging import LEGALogger
logging.setLoggerClass(LEGALogger)

# Send warnings using the package warnings to the logging system
# The warnings are logged to a logger named 'py.warnings' with a severity of WARNING.
# See: https://docs.python.org/3/library/logging.html#integration-with-the-warnings-module
logging.captureWarnings(True)
