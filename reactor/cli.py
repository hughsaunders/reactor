#!/usr/bin/env python

import argparse
import copy
import logging
import signal
import sys
import time
import yaml

import pykka


def load_all_modules(router_module, module_dict):
    router_ref = None
    module_refs = {}

    if router_module is None:
        # if we don't override the router, then we'll hand
        # load a default router
        router_module = 'router'
        router_opts = {'class': 'reactor.modules.router.RouterModule'}
    else:
        router_opts = module_dict.get(router_module, None)

        if router_opts is None or 'class' not in router_opts:
            logging.error('Cannot find router info in config')
            sys.exit(1)

    logging.debug('Loading router module')
    router_ref = load_module(router_opts['class'], 
                             **router_opts.get('config', {}))

    for k, v in module_dict.iteritems():
        if k == router_module:  # don't load again...
            continue

        logging.debug('Loading module %s' % k)
        
        if not 'class' in v:
            logging.error('Missing "class" in section %s' % k)
            sys.exit(1)

        try:
            module_refs[k] = load_module(
                v['class'],router=router_ref,
                config=dict(name=k, **(v.get('config', {}))))
        except Exception as e:
            logging.error('Exception loading module %s: %s' % (k, str(e)))
            quit_app()
            sys.exit(1)

        # check interests and register with router

def load_module(class_name, **kwargs):
    try:
        import_path, import_class = class_name.rsplit('.', 1)
        __import__(import_path)
    except ValueError:
        logging.error('Bad module class name: %s' % (class_name,))
        sys.exit(1)
    except Exception as e:
        logging.error('Exception importing %s: %s' % (
            import_path, str(e)))
        sys.exit(1)

    if not import_path in sys.modules or getattr(
            sys.modules[import_path], import_class, None) is None:
        logging.error('Cannot find %s in %s' % (import_class, import_path))
        sys.exit(1)

    logging.debug('Initializing with %s' % kwargs)
    return getattr(sys.modules[import_path], import_class).start(**kwargs)


def signal_handler(signal, frame):
    print >>sys.stdout, 'SIGINT!'
    quit_app()
    sys.exit(0)


def quit_app():
    pykka.ActorRegistry.stop_all()


def app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='specify config file',
                        default='/etc/reactor/reactor.conf')
    args = parser.parse_args()

    try:
        stream = open(args.config, 'r')
    except IOError as e:
        print >>sys.stdout, 'Error: cannot open config file %s' % args.config
        sys.exit(1)

    with open(args.config, 'r') as stream:
        config = yaml.safe_load(stream)

    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGINT, signal_handler)

    # walk through the config and instantiate all modules
    if not 'modules' in config:
        logging.error('No module section in config')
        sys.exit(1)

    load_all_modules(config.get('router_module', None), config['modules'])
    
    while(1):
        time.sleep(5)
        logging.getLogger().debug('Tick')
