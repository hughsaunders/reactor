#!/usr/bin/env python

import logging

import pykka


# Incoming messages look like this:
#
# {
#   "source": <plugin source name>,
#   "source_type": <source type... http/rabbit/etc>,
#   "source_opts": { ... source specific data },
#   "message": ...
# }
#
class RouterModule(pykka.ThreadingActor):
    def __init__(self, *args, **kwargs):
        super(RouterModule, self).__init__(*args, **kwargs)

        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

    def on_receive(self, message):
        self.logger.debug("Got message: %s" % (message,))


