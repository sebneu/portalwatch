import json
import rdflib

from rdflib import Namespace, BNode, RDF, URIRef, Literal
from rdflib.namespace import FOAF
import urllib.parse
import requests
import urllib.request

ODPW = Namespace('http://data.wu.ac.at/ns/odpw#')
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")

def portals_to_ttl():
    g = rdflib.Graph()
    with open("portals.json") as f:
        portals = json.load(f)

        for p in portals:
            puri = URIRef(p["uri"])
            print(puri)
            g.add((puri, RDF.type, DCAT.Catalog))
            g.add((puri, ODPW.identifier, Literal(p["id"])))
            g.add((puri, ODPW.active, Literal(p["active"])))
            g.add((puri, ODPW.iso, Literal(p["iso"])))
            g.add((puri, ODPW.software, ODPW[p["software"]]))
            if "apiuri" in p:
                g.add((puri, ODPW.api, URIRef(p["apiuri"])))

            g.add((puri, FOAF.homepage, puri))

            # get domain as name
            domain = p["uri"].split("//")[-1].split("/")[0]
            g.add((puri, DCT.title, Literal(domain)))

            # try get catalog.ttl
            if p["software"] == "CKAN":
                try:
                    url = urllib.parse.urljoin(p["apiuri"], "catalog.ttl")

                    response = requests.head(url, timeout=20)
                    if response.status_code >= 200 and response.status_code < 300:
                        g.add((puri, ODPW.rdfendpoint, URIRef(url)))
                        print("TTL: " + url)

                except Exception as e:
                    print("NOTTL")

    g.serialize("new_portals.ttl", format="ttl")


def portal_is_up():
    g = rdflib.Graph()
    g.load("portals.ttl", format="ttl")
    for s in g.subjects(ODPW.active, Literal(True)):
        try:
            c = urllib.request.urlopen(str(s), timeout=30).getcode()
            if c < 200 or c >= 300:
                g.remove((s, ODPW.active, Literal(True)))
                g.add((s, ODPW.active, Literal(False)))
                print(str(s) + ' ' + str(c))
        except:
            g.remove((s, ODPW.active, Literal(True)))
            g.add((s, ODPW.active, Literal(False)))
            print(str(s))

    g.serialize("new_portals.ttl", format="ttl")

if __name__ == '__main__':
    portal_is_up()