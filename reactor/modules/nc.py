#!/usr/bin/env python

# simple notifier for osx notification center.  Requires the
# terminal-notifer application to already be installed.

import copy
import logging
import sys

import pykka
import pync


class NCModule(pykka.ThreadingActor):
    def __init__(self, *args, **kwargs):
        super(NCModule, self).__init__(*args, **kwargs)

        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

    def on_receive(self, message):
        self.logger.debug("Got message: %s" % (message,))

        if not 'text' in message:
            self.logger.warning('No text in notifier message')
            return

        newmessage = copy.deepcopy(message)

        message_txt = newmessage.pop('text')
        for k in newmessage.keys():
            if k not in ['title', 'group', 'activate', 'open',
                         'execute', 'subtitle']:
                newmessage.pop(k)

        if not 'title' in newmessage:
            newmessage['title'] = 'Reactor Message'

        pync.Notifier.notify(message_txt, **newmessage)
