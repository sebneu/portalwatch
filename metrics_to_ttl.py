import hashlib
import rdflib
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, SKOS, RDFS, XSD, FOAF

from fetch import ODPW

DAQ = Namespace("http://purl.org/eis/vocab/daq#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DQV = Namespace("http://www.w3.org/ns/dqv#")
DUV = Namespace("http://www.w3.org/ns/duv#")
OA = Namespace("http://www.w3.org/ns/oa#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SDMX = Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")

PWQ = Namespace("https://data.wu.ac.at/portalwatch/quality#")

PW_AGENT = URIRef("https://data.wu.ac.at/portalwatch")


def general_prov(graph):
    graph.add((PW_AGENT, RDF.type, PROV.SoftwareAgent))
    graph.add((PW_AGENT, RDFS.label, Literal("Open Data Portal Watch")))
    graph.add((PW_AGENT, FOAF.mbox, URIRef("mailto:contact@data.wu.ac.at")))
    graph.add((PW_AGENT, FOAF.homePage, PW_AGENT))


def add_dimensions_and_metrics(g):
    ####################################################################
    ex = PWQ.Existence
    g.add((ex, RDF.type, DQV.Dimension))
    g.add((ex, SKOS.prefLabel, Literal("Existence")))
    g.add((ex, SKOS.definition, Literal("Existence of important information (i.e. exist certain metadata keys)")))

    date = PWQ.Date
    g.add((date, RDF.type, DQV.Metric))
    g.add((date, SKOS.prefLabel, Literal("Date")))
    g.add((date, SKOS.definition, Literal("Does the meta data contain information about creation and modification date of metadata and resources respectively?")))
    g.add((date, RDFS.comment, Literal("Some of the creation and modification date fields for the dataset and resources are empty")))
    g.add((date, DQV.expectedDataType, XSD.double))
    g.add((date, DQV.inDimension, ex))

    rights = PWQ.Rights
    g.add((rights, RDF.type, DQV.Metric))
    g.add((rights, SKOS.prefLabel, Literal("Rights")))
    g.add((rights, SKOS.definition, Literal("Does the meta data contain information about the license of the dataset or resource?")))
    g.add((rights, RDFS.comment, Literal("The dataset has no license information")))
    g.add((rights, DQV.expectedDataType, XSD.double))
    g.add((rights, DQV.inDimension, ex))

    x = PWQ.Preservation
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("Preservation")))
    g.add((x, SKOS.definition, Literal("Does the meta data contain information about format, size or update frequency of the resources?")))
    g.add((x, RDFS.comment, Literal("Information (size, format, mimetype, ..) for preserving/archiving the dataset resource are missing")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, ex))

    x = PWQ.Access
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("Access")))
    g.add((x, SKOS.definition, Literal("Does the meta data contain access information for the resources?")))
    g.add((x, RDFS.comment, Literal("Some of the resources do not have an access URL")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, ex))

    x = PWQ.Discovery
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("Discovery")))
    g.add((x, SKOS.definition, Literal("Does the meta data contain information that can help to discover/search datasets?")))
    g.add((x, RDFS.comment, Literal("Some of the title, description and keyword fields are empty")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, ex))

    x = PWQ.Contact
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("Contact")))
    g.add((x, SKOS.definition, Literal("Does the meta data contain information to contact the data provider or publisher?")))
    g.add((x, RDFS.comment, Literal("Contact information is missing")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, ex))

    ####################################################################
    co = PWQ.Conformance
    g.add((co, RDF.type, DQV.Dimension))
    g.add((co, SKOS.prefLabel, Literal("Conformance")))
    g.add((co, SKOS.definition, Literal("Does information adhere to a certain format if it exist?")))

    x = PWQ.ContactURL
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("ContactURL")))
    g.add((x, SKOS.definition, Literal("Are the available values of contact properties valid HTTP URLs?")))
    g.add((x, RDFS.comment, Literal("The publisher or contact URL is not a syntactically valid URI")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, co))

    x = PWQ.DateFormat
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("DateFormat")))
    g.add((x, SKOS.definition, Literal("Is date information specified in a valid date format?")))
    g.add((x, RDFS.comment, Literal("Some of the creation and modification dates are not in a valid date format")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, co))

    x = PWQ.FileFormat
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("FileFormat")))
    g.add((x, SKOS.definition, Literal("Is the specified file format or media type registered by IANA?")))
    g.add((x, RDFS.comment, Literal("Some of the specified mime types and file format are not registered with IANA (iana.org/)")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, co))

    x = PWQ.ContactEmail
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("ContactEmail")))
    g.add((x, SKOS.definition, Literal("Are the available values of contact properties valid emails?")))
    g.add((date, RDFS.comment, Literal("The publisher or contact Email is not a syntactically valid Email")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, co))

    x = PWQ.License
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("License")))
    g.add((x, SKOS.definition, Literal("Can the license be mapped to the list of licenses reviewed by opendefinition.org?")))
    g.add((x, RDFS.comment, Literal("The specified license could not mapped to the list provided by opendefinition.org")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, co))

    x = PWQ.AccessURL
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("AccessURL")))
    g.add((x, SKOS.definition, Literal("Are the available values of access properties valid HTTP URLs?")))
    g.add((x, RDFS.comment, Literal("The download or access URL is not a syntactically valid URL")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, co))

    #####################################################################
    od = PWQ.OpenData
    g.add((od, RDF.type, DQV.Dimension))
    g.add((od, SKOS.prefLabel, Literal("Open Data")))
    g.add((od, SKOS.definition, Literal("Is the specified format and license information suitable to classify a dataset as open?")))

    x = PWQ.OpenFormat
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("Format Openness")))
    g.add((x, SKOS.definition, Literal("Is the file format based on an open standard?")))
    g.add((x, RDFS.comment, Literal("Some of the specified formats are not considered open")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, od))

    x = PWQ.MachineRead
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("Format machine readability")))
    g.add((x, SKOS.definition, Literal("Can the file format be considered as machine readable?")))
    g.add((x, RDFS.comment, Literal("Some of the specified formats are not considered as machine readable")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, od))

    x = PWQ.OpenLicense
    g.add((x, RDF.type, DQV.Metric))
    g.add((x, SKOS.prefLabel, Literal("License Openneness")))
    g.add((x, SKOS.definition, Literal("Is the used license conform to the open definition?")))
    g.add((x, RDFS.comment, Literal("The specified license is not considered to be open by the opendefinition.org")))
    g.add((x, DQV.expectedDataType, XSD.double))
    g.add((x, DQV.inDimension, od))



def add_identifier(graph):
    
    for metric, value in [(PWQ.Date, "exda"), (PWQ.Rights, "exri"), (PWQ.Preservation, "expr"),
                          (PWQ.Access, "exac"), (PWQ.Discovery, "exdi"), (PWQ.Contact, "exco"),
                          (PWQ.ContactURL, "cocu"), (PWQ.DateFormat, "coda"), (PWQ.FileFormat, "cofo"),
                          (PWQ.ContactEmail, "coce"), (PWQ.License, "coli"), (PWQ.AccessURL, "coac"),
                          (PWQ.OpenFormat, "opfo"), (PWQ.MachineRead, "opma"), (PWQ.OpenLicense, "opli")]:

        graph.add((metric, ODPW.identifier, Literal(value)))


if __name__ == '__main__':
    g = rdflib.Graph()
    add_dimensions_and_metrics(g)
    add_identifier(g)
    general_prov(g)

    g.serialize("metrics.ttl", format="ttl")