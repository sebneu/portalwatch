import re
import dateutil.parser
from rdflib import Namespace, BNode, RDF, URIRef, Literal, RDFS
from rdflib.namespace import FOAF
import hashlib

from utils import ODM_formats

DQV = Namespace('http://www.w3.org/ns/dqv#')
PROV = Namespace('http://www.w3.org/ns/prov#')
PWQ = Namespace('https://data.wu.ac.at/portalwatch/quality#')
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")


email_regex = '[a-zA-Z0-9_\.\+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-\.]+'
email_pattern = re.compile(email_regex)

url_regex= 'https?\:\/\/[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}'
url_pattern = re.compile(url_regex)


OPEN_FORMATS = ['dvi', 'svg'] + ODM_formats.get_non_proprietary()


def is_date(cell):
    try:
        dateutil.parser.parse(cell)
        return True
    except Exception as e:
        return False


def is_email(cell):
    return email_pattern.match(cell)

def is_url(cell):
    return url_pattern.match(cell)



def add_quality_measures(dataset_uri, graph, act):
    # access
    c = 0.0
    exist = 0.0
    conform = 0.0
    for dist_uri in graph.objects(dataset_uri, DCAT.distribution):
        c += 1
        fields = [DCAT.accessURL, DCAT.downloadURL]
        for f in fields:
            v = graph.value(dist_uri, f)
            if v:
                exist += 1
                if is_url(str(v)):
                    conform += 1
                break
    exist = exist/c if c > 0 else 0.0
    conform = conform/exist if exist > 0 else 0.0
    add_measure(graph, exist, PWQ.Access, dataset_uri, act)
    add_measure(graph, conform, PWQ.AccessURL, dataset_uri, act)
    # discovery
    exist = 0.0
    fields = [DCT.title, DCT.description, DCT.keyword]
    for f in fields:
        if graph.value(dataset_uri, f):
            exist += 1
    exist = exist/len(fields)
    add_measure(graph, exist, PWQ.Discovery, dataset_uri, act)
    # contact
    exist = 0.0
    conform_mail = 0.0
    conform_url = 0.0
    fields = [DCAT.contactPoint, DCT.publisher]
    for f in fields:
        v = graph.value(dataset_uri, f)
        if v:
            exist = 1.0
            m = graph.value(v, VCARD.hasEmail)
            if m and is_email(m):
                conform_mail = 1.0
            m = graph.value(v, FOAF.mbox)
            if m and is_email(m):
                conform_mail = 1.0
            m = graph.value(v, FOAF.homepage)
            if m and is_url(m):
                conform_url = 1.0
            m = graph.value(v, VCARD.hasURL)
            if m and is_url(m):
                conform_url = 1.0
    add_measure(graph, exist, PWQ.Contact, dataset_uri, act)
    add_measure(graph, conform_mail, PWQ.ContactEmail, dataset_uri, act)
    add_measure(graph, conform_url, PWQ.ContactURL, dataset_uri, act)
    # rights
    c = 0.0
    exist = 0.0
    for dist_uri in graph.objects(dataset_uri, DCAT.distribution):
        c += 1
        if graph.value(dist_uri, DCT.license):
            exist += 1
    exist = exist/c if c > 0 else 0.0
    add_measure(graph, exist, PWQ.Rights, dataset_uri, act)
    # preservation
    exist = 0.0
    c = 0.0
    fields = [DCT['format'], DCAT.mediaType, DCAT.byteSize]
    for dist_uri in graph.objects(dataset_uri, DCAT.distribution):
        for f in fields:
            c += 1
            if graph.value(dist_uri, f):
                exist += 1
    exist = exist/c if c > 0 else 0.0
    add_measure(graph, exist, PWQ.Preservation, dataset_uri, act)
    # date
    exist = 0.0
    conform = 0.0
    c = 0.0
    fields = [DCT.issued, DCT.modified]
    for f in fields:
        c += 1
        v = graph.value(dataset_uri, f)
        if v:
            exist += 1
            if is_date(v):
                conform += 1
        for dist_uri in graph.objects(dataset_uri, DCAT.distribution):
                c += 1
                dist_v = graph.value(dist_uri, f)
                if dist_v:
                    exist += 1
                    if is_date(dist_v):
                        conform += 1
    exist = exist/c if c > 0 else 0.0
    conform = conform/c if c > 0 else 0.0
    add_measure(graph, exist, PWQ.Date, dataset_uri, act)
    add_measure(graph, conform, PWQ.DateFormat, dataset_uri, act)
    # open format
    openness = 0.0
    c = 0.0
    for dist_uri in graph.objects(dataset_uri, DCAT.distribution):
            c += 1
            v = graph.value(dist_uri, DCT['format'])
            if v and isinstance(v, BNode):
                v = graph.value(dist_uri, RDFS.label)
            if v and v in OPEN_FORMATS:
                # TODO machine readable formats
                openness += 1
    openness = openness/c if c > 0 else 0.0
    add_measure(graph, openness, PWQ.OpenFormat, dataset_uri, act)
    # open license
    c = 0.0
    openness = 0.0
    for dist_uri in graph.objects(dataset_uri, DCAT.distribution):
        c += 1
        v = graph.value(dist_uri, DCT.license)
        if v and v in :
            # TODO license mapping
            openness += 1
    openness = openness / c if c > 0 else 0.0
    add_measure(graph, openness, PWQ.OpenLicense, dataset_uri, act)


def add_measure(graph, value, metric, dataset_uri, activity):
    bnode_hash = hashlib.sha1((dataset_uri.n3() + metric.n3() + str(value)).encode('utf-8'))
    m = BNode(bnode_hash.hexdigest())

    graph.add((m, RDF.type, DQV.QualityMeasurement))
    graph.add((m, RDF.type, PROV.Entity))
    graph.add((m, DQV.value, Literal(value)))
    graph.add((dataset_uri, DQV.hasQualityMeasurement, m))
    graph.add((m, DQV.computedOn, dataset_uri))
    graph.add((m, DQV.isMeasurementOf, metric))
    graph.add((m, PROV.wasGeneratedBy, activity))
    graph.add((activity, PROV.generated, m))
    graph.add((m, PROV.wasDerivedFrom, dataset_uri))

