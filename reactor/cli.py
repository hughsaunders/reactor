#!/usr/bin/env python

import argparse
import logging
import signal
import sys
import time
import yaml

import pykka

import reactor.modules.http
import reactor.modules.router

def app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help="specify config file",
                        default="/etc/reactor/reactor.conf")
    args = parser.parse_args()

    try:
        stream = open(args.config, 'r')
    except IOError as e:
        print >>sys.stdout, 'Error: cannot open config file %s' % args.config
        sys.exit(1)

    with open(args.config, 'r') as stream:
        config = yaml.safe_load(stream)

    logging.basicConfig(level=logging.DEBUG)

    def signal_handler(signal, frame):
        print >>sys.stdout, "SIGINT!"
        pykka.ActorRegistry.stop_all()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)


    router_ref = reactor.modules.router.RouterModule.start()
    http_ref = reactor.modules.http.HttpModule.start(config={'router': router_ref})

    while(1):
        time.sleep(5)
        logging.getLogger().debug('Tick')
