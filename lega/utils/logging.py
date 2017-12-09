# -*- coding: utf-8 -*-

from logging.handlers import SocketHandler


class LogstashHandler(SocketHandler):
    """
    Formats the record according to the formatter. A new line is appended to support streaming listener on Logstash side.
    """
    def makePickle(self, record):
        return (self.format(record) + '\n').encode('utf-8')
