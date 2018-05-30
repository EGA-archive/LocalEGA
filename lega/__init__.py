# -*- coding: utf-8 -*-
# __init__ is here so that we don't collapse in sys.path with another lega module

"""The lega package contains code to start a *Local EGA*. """

__title__ = 'Local EGA'
__version__ = VERSION = '0.1'
__author__ = 'Frédéric Haziza'
#__license__ = 'Apache 2.0'
__copyright__ = 'Local EGA @ NBIS Sweden'

# Set default logging handler to avoid "No handler found" warnings.
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
