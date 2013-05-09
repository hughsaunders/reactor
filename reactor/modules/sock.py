#!/usr/bin/env python

import json
import logging
import os
import socket
import sys
import thread

import pykka


# This module will receive messages, as well as push interests
# up from clients.  Somehow.  System messages?  Not sure
#
class SockModule(pykka.ThreadingActor):
    OUTBOUND = 1
    INBOUND = 2

    def __init__(self, router=None, config=None):
        super(SockModule, self).__init__()

        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

        if router is None:
            self.logger.error('No router specified')
            raise RuntimeError('No router specified')

        self.router = router

        if config is None:
            config = {}

        # we can run in multiple modes
        #
        # A persistent listener.  Client connects, and we
        # push messages from the client into the router.
        #
        #    - listen: true
        #    - port: 32768
        #
        # A persistent listener with interests pushed from
        # clients.
        #    - client_interests: true
        #
        # A forwarding link with fixed interests
        #   - connect: <ip>:port
        #   - interests: ...
        #
        # A forwarding link with client-registered
        # interests
        #
        #  - connect: <ip>:port
        #  - client_interests: true
        #

        self.config = config

        if self.config.get('connect', None) is not None:
            # we are in outbound connect mode
            self.mode = self.OUTBOUND
            if ':' in self.config['connect']:
                host, port = self.config['connect'].split(':')
            else:
                port = 32768
                host = self.config['connect']

            # make the socket connection
            self.outbound_socket = socket.socket(socket.AF_INET,
                                                  socket.SOCK_STREAM)
            self.outbound_socket.connect((host, int(port)))
        else:
            self.mode = self.INBOUND
            self.accept_port = self.config.get('port', 32768)

            self.accept_socket = socket.socket(socket.AF_INET,
                                               socket.SOCK_STREAM)

            self.accept_socket.bind(("0.0.0.0", self.accept_port))

            self.accept_socket.listen(self.config.get('backlog', 5))

            # roll off an accept thread and accept
            # thread-pers
            self.accept_tid = thread.start_new_thread(self.do_accept, ())
            self.logger.debug('Started sock listen on %s' % self.accept_port)

    def do_accept(self):
        while True:
            (cl, addr) = self.accept_socket.accept()
            self.logger.debug('New connection on sock listener')
            ct = thread.start_new_thread(self.do_client, (cl, ))

    def do_client(self, client_socket):
        # we'll do nothing but reads in this thread, and
        # if the client registers interests, we'll spin up
        # an full-on actor for it.
        socketfile = client_socket.makefile()

        while True:
            message = []
            message_len = 0

            # we'll make this kind of line-oriented... read line
            # by line until we get to a line with a "." all by
            # itself.  Kind of lame, but more netcattable than
            # length + data or something.
            while True:
                line = socketfile.readline()

                if len(line) == 0:
                    self.logger.debug('Client disconnected')
                    return

                line = line.rstrip('\n\r')
                self.logger.debug('Got line: %s' % line)

                if line != '.':
                    message_len += len(line)
                    message.append(line)
                else:
                    self.logger.debug('Pushing message to router')
                    message_text = ''.join(message)
                    message_dict = json.loads(message_text)

                    self.router.tell(message_dict)
                    break

                if message_len > 64 * 1024:
                    self.logging.error("Message size exceeded")
                    break

        close(cl)

    def on_receive(self, message):
        self.logger.debug("Got message: %s" % (message,))

        if self.mode == self.OUTBOUND:
            message_text = json.dumps(message) + "\n.\n"

            self.outbound_socket.send(message_text)
