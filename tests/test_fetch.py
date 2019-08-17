import unittest
import fetch
from rdflib import Namespace

DCAT = Namespace("http://www.w3.org/ns/dcat#")

class FetchTestCase(unittest.TestCase):
    def test_fetch_rdf_catalog(self):
        catalog_endpoint = "https://data.gov.uk/catalog.ttl"
        fetch.serialize_ckan_rdf_catalog("data_gov_uk", catalog_endpoint, 1933)

    def test_fetch_sparql_catalog(self):
        catalog_endpoint = "https://www.europeandataportal.eu/sparql"
        fetch.serialize_sparql_catalog("www_europeandataportal_eu", catalog_endpoint, 1933)

if __name__ == '__main__':
    unittest.main()
