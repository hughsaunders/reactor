#!/usr/bin/env python

import logging
import sys

import pykka


class StderrModule(pykka.ThreadingActor):
    def __init__(self, *args, **kwargs):
        super(StderrModule, self).__init__(*args, **kwargs)

        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

    def on_receive(self, message):
        self.logger.debug("Got message: %s" % (message,))
        print >>sys.stderr, message


