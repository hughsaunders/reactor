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
    def __init__(self, router=None, config=None):
        super(RouterModule, self).__init__()

        self.config = config
        if config is None:
            self.config = {}

        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

        self.interests = {}
        self.name_to_ref = {}

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
        for ref, asts in self.interests.iteritems():
            sent_message = False

            if self.config.get('hairpin', False) is False:
                # we want to not consider same ref
                inmod = message['headers'][-1]['source']
                if ref == self.name_to_ref.get(inmod, None):
                    continue

                if ref == self.name_to_ref.get('%s-reverse' % inmod,
                                               None):
                    continue


            for ast in asts:
                if ast.eval_node(message) is True:
                    # we don't want to send the same message twice to
                    # the same plugin.
                    if sent_message is False:
                        ref.tell(message)
                        sent_message = True

    def register_interest(self, name, actor, interest_str):
        try:
            builder = reactor.ast.FilterBuilder(
                reactor.ast.FilterTokenizer(), interest_str)
            ast = builder.build()
        except ValueError as e:
            return False, str(e)

        if not actor in self.interests:
            self.interests[actor] = []

        self.interests[actor].append(ast)

        # in case we want to source route by name
        self.name_to_ref[name] = actor

        return True, 'Success'
