import quality
import logging
import os
import urllib.parse

logger = logging.getLogger(__name__)

import rdflib
from rdflib import URIRef, RDF, Namespace, Literal
from converter import portal_fetch_processors

from utils.snapshots import getCurrentSnapshot

from db import ODPW_GRAPH
from converter.portal_fetch_processors import PROV_ACTIVITY
PROV = Namespace('http://www.w3.org/ns/prov#')

ODPW = Namespace('http://data.wu.ac.at/ns/odpw#')


def fetch_portal_to_dir(p, snapshot, path):
    logger.info("FETCH: " + p['id'])
    portal_ref = rdflib.URIRef(p['uri'])
    portal_api = p['apiuri']
    portal_id = p['id']
    software = p['software']
    proc = portal_fetch_processors.getPortalProcessor(software)

    g = rdflib.Graph()
    proc.fetchAndConvertToDCAT(g, portal_ref, portal_api, snapshot)

    # prov information
    sn_graph = URIRef(ODPW_GRAPH + '/' + str(snapshot))
    activity = rdflib.URIRef(PROV_ACTIVITY + str(snapshot))
    g.add((activity, RDF.type, PROV.Activity))
    g.add((activity, ODPW.snapshot, Literal(int(snapshot))))
    g.add((activity, ODPW.fetched, portal_ref))
    g.add((portal_ref, ODPW.wasFetchedBy, activity))
    g.add((activity, PROV.generated, sn_graph))

    fp = os.path.join(path, portal_id)
    g.serialize(fp + '.ttl', format='ttl')


def fetch_all_portals_to_dir(portals, snapshot, dir):
    logger.info("FETCH ALL - num of portals: " + str(len(portals)))
    path = os.path.join(dir, str(snapshot))
    if not os.path.exists(path):
        os.mkdir(path)

    for p in portals:
        try:
            fetch_portal_to_dir(p, snapshot, path)
        except Exception as e:
            logger.exception("Portal fetch error: " + p['id'] + ', ' + str(e))



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
        portals = db.get_portals().values()

    fetch_all_portals_to_dir(portals, sn, dir)
