import rdflib
from rdflib import URIRef, RDF, Literal
from sqlalchemy import Column, String, Integer, ForeignKey, SmallInteger, TIMESTAMP, BigInteger, ForeignKeyConstraint, \
    Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

import quality
from converter import dataset_converter
from converter.portal_fetch_processors import PROV_ACTIVITY
from db import ODPW_GRAPH
from fetch import PROV, ODPW, PW_AGENT

Base = declarative_base()

from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import csv
import os



tmp=''
tab_portals   =   tmp+'portals'
tab_portalevolution=tmp+'portalevolution'
tab_portalsnapshot=tmp+'portalsnapshot'
tab_portalsnapshotquality=tmp+'portalsnapshotquality'
tab_portalsnapshotdynamicity=tmp+'portalsnapshotdyn'
tab_portalsnapshotfetch=tmp+'portalsnapshotfetch'

tab_formatdist= tmp+"formatdist"
tab_licensedist= tmp+"licensedist"
tab_isodist= tmp+"licensedist"

tab_datasets=tmp+'datasets'
tab_datasetsquality=tmp+'datasetsquality'
tab_datasetsdata=tmp+'datasetsdata'

tab_resources=tmp+'metaresources'
tab_resourcesinfo=tmp+'resourcesinfo'
tab_resourcescrawllog=tmp+'resourcescrawllog'


tab_organisations=tmp+'organisations'
tab_organisationssnapshot=tmp+'organisationsnapshot'

tab_resourceshistory=tmp+'resourceshistory'
tab_resourcesfreshness=tmp+'resourcesfreshness'


class Portal(Base):
    __tablename__ = tab_portals

    id      = Column(String, primary_key=True, index=True,nullable=False)
    uri     = Column(String, nullable=False)
    apiuri  = Column(String)
    software = Column(String(12), nullable=False) # OpenDataSoft, CKAN, Socrata <13
    iso     = Column(String(2), nullable=False)
    active  = Column(Boolean, default=True,nullable=False)
    snapshots = relationship("PortalSnapshot", back_populates="portal")
    snapshotsquality = relationship("PortalSnapshotQuality", back_populates="portal")


class PortalSnapshot(Base):
    __tablename__ = tab_portalsnapshot

    portalid      = Column(String, ForeignKey(tab_portals+'.id'), primary_key=True, index=True,nullable=False)
    snapshot= Column( SmallInteger, primary_key=True)
    portal  = relationship("Portal", back_populates="snapshots")

    start       = Column(TIMESTAMP)
    end         = Column(TIMESTAMP)
    status      = Column(SmallInteger)
    exc         = Column(String)
    datasetcount    = Column(Integer)
    datasetsfetched    = Column(Integer)
    resourcecount   = Column(Integer)
    datasets = relationship("Dataset", back_populates="portalsnapshot")


class PortalSnapshotQuality(Base):
    __tablename__ = tab_portalsnapshotquality

    portalid      = Column(String, ForeignKey(tab_portals+'.id'), primary_key=True, index=True,nullable=False)
    snapshot= Column( SmallInteger, primary_key=True)
    portal  = relationship("Portal", back_populates="snapshotsquality")

    cocu = Column(Float)
    cocuN = Column(Integer)
    coce = Column(Float)
    coceN = Column(Integer)
    coda = Column(Float)
    codaN = Column(Integer)
    cofo = Column(Float)
    cofoN = Column(Integer)
    coli = Column(Float)
    coliN = Column(Integer)
    coac = Column(Float)
    coacN = Column(Integer)
    exda = Column(Float)
    exdaN = Column(Integer)
    exri = Column(Float)
    exriN = Column(Integer)
    expr = Column(Float)
    exprN = Column(Integer)
    exac = Column(Float)
    exacN = Column(Integer)
    exdi = Column(Float)
    exdiN = Column(Integer)
    exte = Column(Float)
    exteN = Column(Integer)
    exsp = Column(Float)
    exspN = Column(Integer)
    exco = Column(Float)
    excoN = Column(Integer)
    opfo = Column(Float)
    opfoN = Column(Integer)
    opma = Column(Float)
    opmaN = Column(Integer)
    opli = Column(Float)
    opliN = Column(Integer)
    datasets=Column(Integer)


class Dataset(Base):
    __tablename__ = tab_datasets

    id           = Column( String, primary_key=True)
    snapshot     = Column( SmallInteger, primary_key=True, index=True)
    portalid     = Column( String, primary_key=True, index=True)
    organisation = Column(String, index=True)
    title        = Column(String, index=True)
    md5          = Column(String, ForeignKey(tab_datasetsdata+'.md5'), index=True)

    __table_args__ = (ForeignKeyConstraint([portalid, snapshot],
                                           [tab_portalsnapshot+'.portalid',tab_portalsnapshot+'.snapshot']),
                      {})

    portalsnapshot = relationship("PortalSnapshot", back_populates="datasets")
    data = relationship("DatasetData", back_populates="dataset")


class DatasetData(Base):
    __tablename__ = tab_datasetsdata

    md5 = Column(String, primary_key=True, index=True, nullable=False)
    raw = Column(JSONB)
    dataset  = relationship("Dataset", back_populates="data")
    resources  = relationship("MetaResource", back_populates="dataset")

    modified = Column(TIMESTAMP)
    created = Column(TIMESTAMP)
    organisation = Column(String, index=True)
    license = Column(String, index=True)



class MetaResource(Base):
    __tablename__ = tab_resources

    uri = Column(String, primary_key=True, index=True)
    md5 = Column(String,ForeignKey(DatasetData.md5), primary_key=True,index=True )
    valid = Column(Boolean)
    format = Column(String)
    media = Column(String)
    size = Column(BigInteger)
    created = Column(TIMESTAMP)
    modified = Column(TIMESTAMP)
    dataset  = relationship("DatasetData", back_populates="resources")


def _row2dict(r):
    data = {}
    for c in r.__table__.columns:
        att = getattr(r, c.name)
        if hasattr(att, 'encode'):
            at = att.encode('utf-8')
        else:
            at = att
        data[c.name] = att
        # if type(att) in [dict, list]:

        # else:
        #    data[c.name] = str(att)

    return data


def row2dict(r):
    if hasattr(r, '_fields'):
        d = {}
        for field in r._fields:
            rf = r.__getattribute__(field)
            if isinstance(rf, Base):
                d.update(_row2dict(rf))
            else:
                d[field] = rf
        return d
    if isinstance(r, Base):
        return _row2dict(r)


def get_portal_snapshot(s, portalid, snapshot):
    q = s.query(PortalSnapshot)
    q = q.filter(PortalSnapshot.portalid == portalid) \
         .filter(PortalSnapshot.snapshot == snapshot)
    return row2dict(q.first())


def get_portal_snapshots(s, portalid):
    q = s.query(PortalSnapshot)
    q = q.filter(PortalSnapshot.portalid == portalid)
    return [row2dict(i) for i in q.all()]


def get_datasets(s, portalid, snapshot):
    q = s.query(DatasetData) \
        .join(Dataset, DatasetData.md5 == Dataset.md5) \
        .filter(Dataset.snapshot == snapshot) \
        .filter(Dataset.portalid == portalid)
    data = [row2dict(r) for r in q.all()]
    return data


def portal_to_ttl(s, portal_uri, portal_api, portal_software, portal_id, snapshot, dir, skip_portal=True):
    filename = os.path.join(dir, portal_id + '.ttl')
    if skip_portal and os.path.exists(filename):
        print(portal_id + ' ' + str(snapshot) + ' already exists.')
        return

    portalsnapshot = get_portal_snapshot(s, portalid=portal_id, snapshot=snapshot)
    datasets = get_datasets(s, portalid=portal_id, snapshot=snapshot)

    portal_activity = URIRef("https://data.wu.ac.at/portalwatch/portal/" + portal_id + '/' + str(snapshot))

    g = rdflib.Graph()
    portal_ref = URIRef(portal_uri)
    # prov information
    g.add((portal_activity, RDF.type, PROV.Activity))
    g.add((portal_activity, PROV.startedAtTime, Literal(portalsnapshot['start'])))
    g.add((portal_activity, PROV.endedAtTime, Literal(portalsnapshot['end'])))
    g.add((portal_activity, PROV.wasAssociatedWith, PW_AGENT))
    g.add((portal_activity, ODPW.snapshot, Literal(int(snapshot))))

    sn_graph = URIRef(ODPW_GRAPH + '/' + str(snapshot))
    sn_activity = rdflib.URIRef(PROV_ACTIVITY + str(snapshot))
    g.add((sn_activity, RDF.type, PROV.Activity))
    g.add((sn_activity, PROV.generated, sn_graph))

    g.add((portal_activity, ODPW.fetched, portal_ref))
    g.add((portal_ref, ODPW.wasFetchedBy, portal_activity))
    g.add((portal_activity, PROV.wasStartedBy, sn_activity))

    if portal_software == 'SPARQL' or portal_software == 'CKANDCAT':
        portal_software = 'CKAN'
    for d in datasets:
        dataset_to_ttl(d['raw'], g, portal_ref, portal_api, portal_software, portal_activity)

    g.serialize(filename, format='ttl')


def dataset_to_ttl(datasetdata, graph, portal_uri, portal_api, portal_software, activity):
    dataset_ref = dataset_converter.dict_to_dcat(datasetdata, graph, portal_uri, portal_api, portal_software)
    quality.add_quality_measures(dataset_ref, graph, activity)



#--*--*--*--*
def help():
    return "Postgres DB Exporter"


def name():
    return 'DBExport'

def setupCLI(pa):
    pa.add_argument('-u', '--user')
    pa.add_argument('-p', '--password')
    pa.add_argument('--host')
    pa.add_argument('--port')
    pa.add_argument('--db')
    pa.add_argument('--portal')
    pa.add_argument('--file')


def cli(config, db, args):
    conn_string = "postgresql://"
    conn_string += args.user
    conn_string += ":" + args.password
    conn_string += "@" + args.host
    conn_string += ":" + str(args.port)
    conn_string += "/" + args.db
    print("Connecting DB")
    engine = create_engine(conn_string, pool_size=20, client_encoding='utf8', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    dir = config['fetch']['dir']

    portalid = args.portal
    p = db.get_portal(portalid)
    if args.file:
        with open(args.file) as f:
            csvr = csv.reader(f)
            next(csvr)
            for row in csvr:
                snapshot = int(row[0])
                path = os.path.join(dir, str(snapshot))
                if not os.path.exists(path):
                    os.mkdir(path)
                portal_to_ttl(session, p['uri'], p['apiuri'], p['software'], portalid, snapshot, path)
