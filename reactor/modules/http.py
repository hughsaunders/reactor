#!/usr/bin/env python

import BaseHTTPServer
import cgi
import json
import logging
import sys
import thread
import urlparse

import pykka
import reactor.util


class HttpModule(pykka.ThreadingActor):
    def __init__(self, router=None, config=None):
        super(HttpModule, self).__init__()
        classname = self.__class__.__name__.lower()

        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

        if router is None:
            self.logger.error('No router specified.  Abort')
            raise RuntimeError('No router specified')

        if config is None:
            config = {}

        port = int(config.get('port', 8080))

        self.http_server = BaseHTTPServer.HTTPServer(
            ('', port),
            lambda *args, **kwargs: HttpHandler(router=router,
                                           config=config,
                                           *args, **kwargs))

        self.logger.debug('Started web server on port %d' % port)
        self.must_quit = False
        self.tid = thread.start_new_thread(self.do_thread, ())

    def do_thread(self):
        while not self.must_quit:
            self.http_server.handle_request()

        self.logger.debug('Cleanly exiting http thread')


class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

        config = {}
        if 'config' in kwargs:
            config = kwargs.pop('config')

        assert('router' in kwargs)
        self.router = kwargs.pop('router')

        self.config = config

        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def log_message(self, format, *args):
        self.logger.info(format % args)

    def do_POST(self):
        self.logger.debug('Got POST')
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write('Submitted\n')

        message_opts = {'path': self.path}
        message_data = {}

        # we ought to have some data here...
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        length = int(self.headers.getheader('content-length', None))

        if length is None:
            self.logging.warning('No content length. Ignoring.')
            return

        message_txt = self.rfile.read(length)
        self.logger.debug('message: %s' % (message_txt, ))

        if ctype == 'application/json' or \
           ctype == 'text/json':
            message_data = json.loads(message_txt)
        elif ctype == 'application/x-www-form-urlencoded':
            # This is completely broken, and only works on
            # github.  Should be abstracted
            message_data = json.loads(urlparse.parse_qs(message_txt)['payload'][0])
        else:
            self.logger.debug('content type: %s. Ignoring' % (ctype,))
            return

        message = reactor.util.message_wrap(message_data, self.config['name'],
                                            'http', source_opts = message_opts)

        if self.router is not None:
            self.router.tell(message)
        else:
            self.logger.debug("No router... dropping message")
