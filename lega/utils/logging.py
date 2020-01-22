# -*- coding: utf-8 -*-
"""Logs Formatter."""

from logging import Formatter
from logging.handlers import DatagramHandler, SocketHandler
import json
import re

class BaseHandler():
    """Base Log Handler.

    We do not use pickle.dumps for the result.
    We only send it as bytes (adding a newline).
    """

    def makePickle(self, record):
        """Create python pickle."""
        # the parent makePickle uses pickle.dumps
        # which sends more than the formatted record
        # See https://github.com/python/cpython/blob/3.8/Lib/logging/handlers.py#L585-L605
        # Instead, we only format the record and send it as bytes, along with a newline terminator
        return self.format(record).encode('utf-8') + b'\n'

class UDPHandler(DatagramHandler, BaseHandler):
    """UDP Log Handler."""
    pass

class TCPHandler(SocketHandler, BaseHandler):
    """TCP Log Handler."""
    pass


_FIELDS = re.compile(r'\((.+?)\)', re.IGNORECASE)

class JSONFormatter(Formatter):
    """Json Logs formatting."""

    def __init__(self, *args, **kwargs):
        """Initialize formatter."""
        Formatter.__init__(self, *args, **kwargs)
        self._fields = _FIELDS.findall(self._fmt)

    def format(self, record):
        """Format a log record and serializes to json."""
        _record = {}

        for field in self._fields:
            if field == "asctime":
                _record[field] = self.formatTime(record, self.datefmt)
            elif field == "message":
                _record[field] = record.getMessage()
            else:
                attr = getattr(record, field, None)
                assert attr, f"Attribute {field} missing in LogRecord"
                _record[field] = attr

        if record.exc_info:
            _record['exc_info'] = self.formatException(record.exc_info)

        if record.stack_info:
            _record['stack_info'] = self.formatStack(record.stack_info)

        return json.dumps(_record)
 
