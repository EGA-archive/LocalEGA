# -*- coding: utf-8 -*-
"""Logs Formatter."""

from logging import Formatter, Logger, currentframe
from logging.handlers import SocketHandler as handler  # or DatagramHandler ?
import json
import re


class LEGAHandler(handler):
    """Formats the record according to the formatter.

    A new line is sent to support Logstash input plugin.
    """

    terminator = b'\n'

    def send(self, s):
        """Register SocketHandler ``send`` plus the class terminator (newline)."""
        super().send(s)
        if self.sock is not None:
            self.sock.sendall(self.terminator)

    def makePickle(self, record):
        """Create python pickle."""
        # pickle.dumps creates problem for logstash
        # to parse a JSON formatted string.
        # Especially when the bytes length is prepended.
        return self.format(record).encode('utf-8')


class JSONFormatter(Formatter):
    """Json Logs formatting.

    Mainly used for ELK stack.
    """

    def __init__(self, *args, **kwargs):
        """Initialize formatter."""
        Formatter.__init__(self, *args, **kwargs)
        standard_formatters = re.compile(r'\((.+?)\)', re.IGNORECASE)
        self._fields = standard_formatters.findall(self._fmt)

    def format(self, record):
        """Format a log record and serializes to json."""
        log_record = {}

        for field in self._fields:
            if field == "asctime":
                log_record[field] = self.formatTime(record, self.datefmt)
            elif field == "message":
                log_record[field] = record.getMessage()
            else:
                assert hasattr(record, field), f"Attribute {field} missing in LogRecord"
                log_record[field] = getattr(record, field)

        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)

        if record.stack_info:
            log_record['stack_info'] = self.formatStack(record.stack_info)

        return json.dumps(log_record)


def get_correlation_id(stacklevel=10):
    """Retrieve the correlation id from caller's frame.

    We inspect ``stacklevel`` levels in the stack of callers.

    :returns: None if not found, the correlation id if found
    :rtype: str or None
    """
    f = currentframe()
    while f and stacklevel > 0:
        locs = f.f_locals
        cid = locs.get('correlation_id')
        if cid:  # gotcha
            return cid
        f = f.f_back  # caller frame
        stacklevel -= 1
    return None


class LEGALogger(Logger):
    """Logger with a correlation id injected in the log records.

    If the correlation id is specified in the ``extra`` dictionary, we
    inject its value. If not, we try to find it in the local variables
    of the calling frames. If none of the previous cases happen, we
    use the value '--------'.

    """

    def makeRecord(self, *args, **kwargs):
        """Specialized record with correlation_id."""
        rv = super(LEGALogger, self).makeRecord(*args, **kwargs)

        # Adding correlation_id if not already there
        if 'correlation_id' in rv.__dict__.keys():
            return rv
        rv.__dict__['correlation_id'] = get_correlation_id() or '--------'
        return rv
