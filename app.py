import sys
import time
import argparse
import logging
import yaml
from yaml import Loader
import db


import fetch
from ui import webui


logger = logging.getLogger(__name__)

submodules=[fetch, webui]

def start(argv):
    start = time.time()
    pa = argparse.ArgumentParser(description='Open Portal Watch toolset.', prog='odpw')

    logg=pa.add_argument_group("Logging")
    logg.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING
    )
    logg.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
        default=logging.WARNING
    )

    config=pa. add_argument_group("Config")
    config.add_argument('-c', '--config', help="config file", dest='config', default='config.yaml')

    sp = pa.add_subparsers(title='Modules', description="Available sub modules")
    for sm in submodules:
        smpa = sp.add_parser(sm.name(), help=sm.help())
        sm.setupCLI(smpa)
        smpa.set_defaults(func=sm.cli)

    args = pa.parse_args(args=argv)
    try:
        with open(args.config) as f_conf:
            config = yaml.load(f_conf, Loader=Loader)
    except Exception as e:
        print("Exception during config initialisation:" + str(e))
        return

    logging.basicConfig(level=args.loglevel)

    try:
        logger.info("CMD ARGS: " + str(args))

        dbc = db.DB(config['endpoint'])
        args.func(config, dbc, args)
    except Exception as e:
        logger.fatal("Uncaught Exception: " + str(e))

    end = time.time()
    secs = end - start
    msecs = secs * 1000
    logger.info("END MAIN. Time elapsed: " + str(msecs))


if __name__ == "__main__":
    start(sys.argv[1:])
