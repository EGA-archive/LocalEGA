# -*- coding: utf-8 -*-
"""Logs Formatter."""

from logging import Formatter
import json
import re

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

        return json.dumps(_record) + '\n'  # adding a new line already here
