import logging
import sys


class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self._configure_stream_handler()

    def _configure_stream_handler(self):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stream_handler)
