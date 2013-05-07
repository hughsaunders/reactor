#!/usr/bin/env python

import BaseHTTPServer
import cgi
import json
import logging
import thread
import urlparse


import pykka


class HttpModule(pykka.ThreadingActor):
    def __init__(self, config=None):
        super(HttpModule, self).__init__()

        if config is None:
            config = {}

        if 'port' in config:
            port = int(config['port'])
        else:
            port = 8080
        
        classname = self.__class__.__name__.lower()

        self.logger = logging.getLogger('%s.%s' % (__name__, classname))
        
        self.http_server = BaseHTTPServer.HTTPServer(
            ('', port), 
            lambda *args, **kwargs: HttpHandler(config=config, *args, **kwargs))

        self.logger.debug('Started web server on port %d' % port)
        self.must_quit = False
        self.tid = thread.start_new_thread(self.do_thread, ())


    def do_thread(self):
        while not self.must_quit:
            self.http_server.handle_request()

        self.logger.debug('Cleanly exiting http thread')


class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        if 'config' in kwargs:
            config = kwargs.pop('config')
        else:
            config = {}

        classname = self.__class__.__name__.lower()
        self.logger = logging.getLogger('%s.%s' % (__name__, classname))

        self.logger.error('args: %s' % (args,))
        self.logger.error('kwargs: %s' % (kwargs,))

        if config is None:
            config = {}

        if 'source_name' in config:
            self.source_name = config['source_name']
        else:
            self.source_name = 'http'

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
        if ctype == 'application/json' or \
           ctype == 'text/json':
            length = int(self.headers.getheader('content-length', None))
            if length is not None:
                message_data = json.loads(self.rfile.read(length))
            else:
                self.warn('HTTP 0.9?  Really?')
        
        message = {'source_type': 'http',
                   'source_name': self.source_name,
                   'source_opts': message_opts,
                   'message': message_data}

        if 'router' in self.config:
            self.config['router'].tell(message)

