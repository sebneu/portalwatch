import quality
import logging
import os
import urllib.parse

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

import rdflib
from converter import portal_fetch_processors
from utils.snapshots import getCurrentSnapshot


def fetch_portal_to_dir(p, snapshot, path):
    portal_ref = rdflib.URIRef(p['uri'])
    portal_api = p['apiuri']
    portal_id = p['pid']
    software = p['software']
    proc = portal_fetch_processors.getPortalProcessor(software)

    g = rdflib.Graph()
    proc.fetchAndConvertToDCAT(g, portal_ref, portal_api, snapshot)

    fp = os.path.join(path, portal_id)
    g.serialize(fp + '.ttl', format='ttl')


def fetch_all_portals_to_dir(portals, snapshot, dir):
    path = os.path.join(dir, str(snapshot))
    if not os.path.exists(path):
        os.mkdir(path)

    for p in portals:
        try:
            fetch_portal_to_dir(p, snapshot, path)
        except Exception as e:
            logger.exception("Portal fetch error: " + p['pid'] + ', ' + str(e))



#--*--*--*--*
def help():
    return "Fetch all metadata from the portals"


def name():
    return 'Fetch'


def setupCLI(pa):
    pa.add_argument('--pid', dest='portalid', help="Fetch a specific portal ID")


def cli(config, db, args):
    sn = getCurrentSnapshot()
    dir = config['fetch']['dir']

    if args.portalid:
        portals = [db.get_portal(id=args.portalid)]
    else:
        portals = db.get_portals()

    fetch_all_portals_to_dir(portals, sn, dir)
