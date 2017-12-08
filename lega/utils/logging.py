# -*- coding: utf-8 -*-

from logging.handlers import SocketHandler
import ssl


class LogstashHandler(SocketHandler):
    """
    Sends output to an optionally encrypted streaming Logstash TCP listener.
    """
    def __init__(self, host, port, keyfile=None, certfile=None, ca_certs=None, ssl=True):
        SocketHandler.__init__(self, host, port)
        self.keyfile = keyfile
        self.certfile = certfile
        self.ca_certs = ca_certs
        self.ssl = ssl

    def makeSocket(self, timeout=1):
        s = SocketHandler.makeSocket(self, timeout)
        if self.ssl:
            return ssl.wrap_socket(s, keyfile=self.keyfile, certfile=self.certfile, ca_certs=self.ca_certs)
        return s

    """
    Formats the record according to the formatter. A new line is appended to support streaming listener on Logstash side.
    """
    def makePickle(self, record):
        return self.format(record) + "\n"