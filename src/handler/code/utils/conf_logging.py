# -*- coding: utf-8 -*-
"""Handling correlation id across all logs."""

from logging import Logger

class _wrapper():
    """Wrapper class for the correlation id."""

    value = None

    def get(self):
        return self.value

    def set(self, v):
        self.value = v


_cid = _wrapper()


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
        rv.__dict__['correlation_id'] = _cid.get() or '--------'
        return rv


