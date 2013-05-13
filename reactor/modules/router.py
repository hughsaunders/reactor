#!/usr/bin/env python

import logging

import reactor.ast
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

        self.interests = []


    def on_receive(self, message):
        self.logger.debug("Got message: %s" % (message,))

        assert('headers' in message)
        assert(len(message['headers']) > 0)
        assert('ttl' in message['headers'][-1])

        # it should be properly wrapped, so check ttl.
        # some defaults here?
        last_ttl = message['headers'][-1]['ttl']

        if last_ttl < 1:
            self.logger.warning('TTL Drop: message loop')
            return

        # walk through our registered interests and see if anyone
        # wants it.
        for actor, ast in self.interests:
            if ast.eval_node(message) is True:
                actor.tell(message)


    def register_interest(self, actor, interest_str):
        try:
            builder = reactor.ast.FilterBuilder(
                reactor.ast.FilterTokenizer(), interest_str)
            ast = builder.build()
        except ValueError as e:
            return False, str(e)

        self.interests.append((actor, ast))
        return True, 'Success'
