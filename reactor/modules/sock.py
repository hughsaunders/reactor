#!/usr/bin/env python

import json
import logging
import os
import socket
import sys
import thread

import pykka
import reactor.util
import reactor.modules.router



class SockReverseModule(pykka.ThreadingActor):
    def __init__(self, outbound_socket, name='adhoc-socket-reverse'):
        # this is the listener for a remote system that
        # is using remote sourced registrations.  If we
        # get something from the router, we'll pass it
        # across the wire to the remote system, using
        # regular sockmodule semantics.
        super(SockReverseModule, self).__init__()

        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))
        self.outbound_socket = outbound_socket
        self.name = name

    def on_receive(self, message):
        # we write this in regular socket format
        self.logger.debug("Got message: %s" % (message,))

        message = reactor.util.message_wrap(message, self.name,
                                            'socket')

        message_text = 'MESSAGE\n' + json.dumps(message) + "\n.\n"
        self.outbound_socket.send(message_text)


# This module will receive messages, as well as push interests
# up from clients.  Somehow.  System messages?  Not sure
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
        # clients. (INBOUND)
        #    - client_interests: true
        #
        # A forwarding link with fixed interests (OUTBOUND)
        #   - connect: <ip>:port
        #   - interests: ...
        #
        # A forwarding link with client-registered
        # interests (OUTBOUND)
        #
        #  - connect: <ip>:port
        #  - client_interests: true

        self.config = config
        self.config['client_interests'] = self.config.get(
            'client_interests', False)

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

            if 'interests' in self.config:
                # dump out our interests on the line
                message_text = 'INTEREST\n' + json.dumps(self.config['interests']) + "\n.\n"
                self.outbound_socket.send(message_text)

                # we need to spin up a thread for reading stuff that
                # comes back
                self.accept_tid = thread.start_new_thread(
                    self.do_client, (self.outbound_socket,))
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

    def get_block(self, fileish):
        message = []
        message_len = 0
        message_too_long = False

        while True:
            line = fileish.readline()

            if len(line) == 0:
                self.logger.debug('Client disconnected')
                return None

            line = line.rstrip('\n\r')
            self.logger.debug('Got line: %s' % line)

            if line != '.':
                if message_len > 64 * 1024:
                    if message_too_long is False:
                        self.logger.warning('Data too long... absorbing')
                        message_too_long = True
                else:
                    message_len += len(line)
                    message.append(line)
            else:
                self.logger.debug('Finished receiving data block')
                if message_too_long:  # going to be broken, we'll skip it.
                    return None

                message_text = ''.join(message)
                try:
                    message_dict = json.loads(message_text)
                except ValueError:
                    return None

                return message_dict

    def do_client(self, client_socket):
        # we'll do nothing but reads in this thread, and
        # if the client registers interests, we'll spin up
        # an full-on actor for sonds to it.
        socketfile = client_socket.makefile()
        interest_agent = None

        while True:
            line = socketfile.readline()

            if len(line) == 0:
                self.logger.debug('Client disconnected')
                return

            line = line.rstrip('\n\r')
            self.logger.debug('Got Line: %s' % line)

            if line.lower() == 'message':
                message_dict = self.get_block(socketfile)
                if message_dict is not None:
                    self.router.tell(reactor.util.message_wrap(
                        message_dict, self.config['name'], 'socket'))

            elif line.lower() == 'interest':
                if self.config['client_interests'] is False:
                    self.logger.warn('Ignoring client interests by config')
                else:
                    interest_array = self.get_block(socketfile)
                    if interest_array is not None:
                        # here, we need to either make a new
                        # actor with new interests, or update the
                        # interests in an existing actor

                        # if we are an INBOUND server, we need to make a
                        # new agent as a per-connection thing
                        if self.mode == self.INBOUND:
                            if interest_agent is None:
                                self.logger.debug('Starting new agent')
                                interest_agent = SockReverseModule.start(
                                    client_socket,
                                    name='%s-reverse' % self.config['name'])

                            for interest in interest_array:
                                self.logger.debug('Registering interest')
                                self.router.proxy().register_interest(
                                    '%s-reverse' % self.config['name'],
                                    interest_agent, interest)
                        else:
                            self.logger.debug('skipping INTEREST on OUTBOUND sock')

            elif line.lower() == 'quit':
                self.logger.debug('Exiting listener at client request')
                break

        self.logger.debug('Client listener exiting')
        close(cl)

    def on_receive(self, message):
        self.logger.debug("Got message: %s" % (message,))

        if self.mode == self.OUTBOUND:
            message_text = 'MESSAGE\n' + json.dumps(message) + "\n.\n"

            self.outbound_socket.send(message_text)
