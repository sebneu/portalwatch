import unittest
import fetch
from converter import portal_fetch_processors
from rdflib import Namespace
import rdflib
import os

DCAT = Namespace("http://www.w3.org/ns/dcat#")

class FetchTestCase(unittest.TestCase):
    def test_fetch_rdf_catalog(self):
        catalog_endpoint = "https://data.gov.uk/catalog.ttl"
        fetch.serialize_ckan_rdf_catalog("data_gov_uk", catalog_endpoint, 1933)

    def test_fetch_sparql_catalog(self):
        catalog_endpoint = "https://www.europeandataportal.eu/sparql"
        fetch.serialize_sparql_catalog("www_europeandataportal_eu", catalog_endpoint, 1933)


    def test_ckan_catalog(self):
        g = rdflib.Graph()
        portal_ref = rdflib.URIRef("http://rotterdamopendata.nl")
        portal_api = "http://rotterdamopendata.nl/"
        pid = "www_rotterdamopendata_nl"
        snapshot = 1934
        ckan = portal_fetch_processors.CKAN()
        ckan.fetchAndConvertToDCAT(g, portal_ref, portal_api, snapshot)

        dir = 'dumps'
        p = os.path.join(dir, str(snapshot))
        if not os.path.exists(p):
            os.mkdir(p)
        fp = os.path.join(p, pid)
        g.serialize(fp + '.ttl', format='ttl')


    def test_opendatasoft_catalog(self):
        g = rdflib.Graph()
        p = "https://dataratp.opendatasoft.com"
        portal_ref = rdflib.URIRef(p)
        portal_api = p
        pid = "dataratp_opendatasoft_com"
        snapshot = 1934
        ckan = portal_fetch_processors.OpenDataSoft()
        ckan.fetchAndConvertToDCAT(g, portal_ref, portal_api, snapshot)

        dir = 'dumps'
        p = os.path.join(dir, str(snapshot))
        if not os.path.exists(p):
            os.mkdir(p)
        fp = os.path.join(p, pid)
        g.serialize(fp + '.ttl', format='ttl')


    def test_socrata_catalog(self):
        g = rdflib.Graph()
        p = "https://opendata.socrata.com"
        portal_ref = rdflib.URIRef(p)
        portal_api = p
        pid = "opendata_socrata_com"
        snapshot = 1934
        ckan = portal_fetch_processors.Socrata()
        ckan.fetchAndConvertToDCAT(g, portal_ref, portal_api, snapshot)

        dir = 'dumps'
        p = os.path.join(dir, str(snapshot))
        if not os.path.exists(p):
            os.mkdir(p)
        fp = os.path.join(p, pid)
        g.serialize(fp + '.ttl', format='ttl')





if __name__ == '__main__':
    unittest.main()
