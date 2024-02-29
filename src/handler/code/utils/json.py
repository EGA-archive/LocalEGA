import logging

from json import loads as parse_json

from .exceptions import FEGASystemError

LOG = logging.getLogger(__name__)

class FEGAMessage:
    __parsed = None
    __content = None
    __message = None

    def __init__(self, message):
        self.__message = message

    def __getattr__(self, item):
        return getattr(self.__message, item)

    @property
    def content(self):
        if self.__content is None:
            self.__content = self.body.decode()
        return self.__content

    @property
    def parsed(self):
        """Return a JSON deserializing of itself."""
        if self.__parsed is None:
            # if message.header.properties.content_type != 'application/json':
            #     raise FEGASystemError('Not an "application/json" message')
            try:
                self.__parsed = parse_json(self.content)
            except Exception as e:
                LOG.error('Malformatted JSON: %s', e)
                raise FEGASystemError(repr(e))

        return self.__parsed

