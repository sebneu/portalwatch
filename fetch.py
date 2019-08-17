import quality
import logging
import os
import urllib.parse

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


import rdflib
from rdflib import Namespace, URIRef, RDF


HYDRA = Namespace("http://www.w3.org/ns/hydra/core#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")


def fetch_ckan_rdf_catalog(endpoint, format="ttl"):
    logger.debug('Fetching CKAN portal via RDF endpoint: ' + endpoint)
    g = rdflib.Graph()
    g.parse(endpoint, format=format)
    yield g
    cur = g.value(predicate=RDF.type, object=HYDRA.PagedCollection)
    next_page = g.value(subject=cur, predicate=HYDRA.nextPage)
    page = 0
    while next_page:
        page += 1
        if page % 10 == 0:
            logger.debug('Processed pages:' + str(page))

        p = str(next_page)
        g = rdflib.Graph()
        g.parse(p, format=format)
        yield g
        next_page = g.value(subject=URIRef(next_page), predicate=HYDRA.nextPage)

    logger.debug('Total pages:' + str(page))
    logger.info('Fetching finished')


def serialize_ckan_rdf_catalog(pid, endpoint, snapshot, dir='dumps'):
    p = os.path.join(dir, str(snapshot))
    if not os.path.exists(p):
        os.mkdir(p)
    fp = os.path.join(p, pid)
    for i, g in enumerate(fetch_ckan_rdf_catalog(endpoint)):
        for d in g.subjects(RDF.type, DCAT.Dataset):
            quality.add_quality_measures(d, g, snapshot)
        g.serialize(fp + str(i) + '.ttl', format='ttl')


def serialize_sparql_catalog(pid, endpoint, snapshot, dir='dumps'):
    p = os.path.join(dir, str(snapshot))
    if not os.path.exists(p):
        os.mkdir(p)
    fp = os.path.join(p, pid)

    url = endpoint + "?format=text/turtle&query="
    query = """
    construct {?dataset a dcat:Dataset}  {
        ?dataset a dcat:Dataset.
    }
    """

    limit = 10000
    offset = 0
    download_url = url + urllib.parse.quote(query + " OFFSET " + str(offset) + " LIMIT " + str(limit))

    g = rdflib.Graph()
    g.parse(download_url, format='ttl')

    for dataset_uri in g.subjects(RDF.type, DCAT.Dataset):
        construct_query = """
        CONSTRUCT {{ <{0}> ?p ?o. ?o ?q ?r}}
        WHERE {{
        <{0}> a dcat:Dataset.
        <{0}> ?p ?o
        OPTIONAL {{?o ?q ?r}}
        }}
        """.format(str(dataset_uri))

        ds_url = url + urllib.parse.quote(construct_query)
        g.parse(ds_url, format='ttl')

        quality.add_quality_measures(dataset_uri, g, snapshot)
        offset = offset + limit

    g.serialize(fp + '.ttl', format='ttl')

