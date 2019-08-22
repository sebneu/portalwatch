import quality
import logging
import os
import urllib.parse
from datetime import datetime

logger = logging.getLogger(__name__)

import rdflib
from rdflib import URIRef, RDF, Namespace, Literal
from converter import portal_fetch_processors

from utils.snapshots import getCurrentSnapshot

from db import ODPW_GRAPH
from converter.portal_fetch_processors import PROV_ACTIVITY

PROV = Namespace('http://www.w3.org/ns/prov#')

ODPW = Namespace('http://data.wu.ac.at/ns/odpw#')

PW_AGENT = URIRef("https://data.wu.ac.at/portalwatch")



def fetch_portal_to_dir(p, snapshot, path, format='ttl', skip_portal=True):
    logger.info("FETCH: " + p['id'])
    portal_ref = rdflib.URIRef(p['uri'])
    portal_api = p['apiuri']
    portal_id = p['id']
    software = p['software']
    fp = os.path.join(path, portal_id) + '.' + format
    # skip portal if exists
    if skip_portal and os.path.exists(fp):
        logger.info("File exists, skip portal: " + p['id'])

    # log execution time
    start_time = datetime.now()
    portal_activity = URIRef("https://data.wu.ac.at/portalwatch/portal/" + portal_id + '/' + str(snapshot))

    proc = portal_fetch_processors.getPortalProcessor(software)
    g = rdflib.Graph()
    proc.fetchAndConvertToDCAT(g, portal_ref, portal_api, snapshot, portal_activity)

    end_time = datetime.now()

    # prov information
    g.add((portal_activity, RDF.type, PROV.Activity))
    g.add((portal_activity, PROV.startedAtTime, Literal(start_time)))
    g.add((portal_activity, PROV.endedAtTime, Literal(end_time)))
    g.add((portal_activity, PROV.wasAssociatedWith, PW_AGENT))
    g.add((portal_activity, ODPW.snapshot, Literal(int(snapshot))))

    sn_graph = URIRef(ODPW_GRAPH + '/' + str(snapshot))
    sn_activity = rdflib.URIRef(PROV_ACTIVITY + str(snapshot))
    g.add((sn_activity, RDF.type, PROV.Activity))
    g.add((sn_activity, PROV.generated, sn_graph))

    g.add((portal_activity, ODPW.fetched, portal_ref))
    g.add((portal_ref, ODPW.wasFetchedBy, portal_activity))
    g.add((portal_activity, PROV.wasStartedBy, sn_activity))

    # serialize
    g.serialize(fp, format=format)


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
