from sqlalchemy import Column, String, Integer, ForeignKey, SmallInteger, TIMESTAMP, BigInteger, ForeignKeyConstraint, \
    Boolean, func, select, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
Base = declarative_base()

from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import and_

import argparse
import sys
import csv



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


def _get_measures_for_dataset(portal, snapshot, datasetdata, datasetquality):
    graph = rdflib.Graph()
    # write dcat dataset into graph
    dataset_converter.dict_to_dcat(datasetdata, portal, graph=graph)
    measures_g = rdflib.Graph()
    ds_id = graph.value(predicate=RDF.type, object=DCAT.Dataset)
    dataset_quality_to_dqv(measures_g, ds_id, datasetquality, snapshot)
    return measures_g, ds_id

def get_measures_for_dataset(portal, snapshot, datasetdata, datasetquality):
    measures_g, datasetref = _get_measures_for_dataset(portal, snapshot, datasetdata, datasetquality)
    return measures_g


def dataset_quality_to_dqv(graph, ds_id, datasetquality, snapshot, fetch_activity=None):
    sn_time = utils_snapshot.tofirstdayinisoweek(snapshot)

    # BNodes: ds_id + snapshot + metric + value
    # add quality metrics to graph
    # TODO should we use portalwatch URI?
    for metric, value in [(PWQ.Date, datasetquality.exda), (PWQ.Rights, datasetquality.exri), (PWQ.Preservation, datasetquality.expr),
                          (PWQ.Access, datasetquality.exac), (PWQ.Discovery, datasetquality.exdi), (PWQ.Contact, datasetquality.exco),
                          (PWQ.ContactURL, datasetquality.cocu), (PWQ.DateFormat, datasetquality.coda), (PWQ.FileFormat, datasetquality.cofo),
                          (PWQ.ContactEmail, datasetquality.coce), (PWQ.License, datasetquality.coli), (PWQ.AccessURL, datasetquality.coac),
                          (PWQ.OpenFormat, datasetquality.opfo), (PWQ.MachineRead, datasetquality.opma), (PWQ.OpenLicense, datasetquality.opli)]:
        # add unique BNodes

        quality.add_measure(graph, value, metric, ds_id, act)

        bnode_hash = hashlib.sha1(ds_id.n3() + str(snapshot) + metric.n3() + str(value))
        m = BNode(bnode_hash.hexdigest())

        graph.add((m, DQV.isMeasurementOf, metric))
        graph.add((m, DQV.value, Literal(value)))

        # add additional triples
        graph.add((ds_id, DQV.hasQualityMeasurement, m))
        graph.add((m, RDF.type, DQV.QualityMeasurement))
        graph.add((m, DQV.computedOn, ds_id))
        if fetch_activity:
            # add prov to each measure
            quality_prov(m, ds_id, sn_time, fetch_activity, graph)


def start(argv):
    pa = argparse.ArgumentParser(description='Postgres DB Exporter')
    pa.add_argument('-u', '--user')
    pa.add_argument('-p', '--password')
    pa.add_argument('--host')
    pa.add_argument('--port')
    pa.add_argument('--db')
    pa.add_argument('--portal')

    args = pa.parse_args(args=argv)

    conn_string = "postgresql://"
    conn_string += args.user
    conn_string += ":" + args.password
    conn_string += "@" + args.host
    conn_string += ":" + str(args.port)
    conn_string += "/" + args.db
    print("Connecting DB")
    engine = create_engine(conn_string, pool_size=20, client_encoding='utf8', echo=False)
    #connection = engine.connect()
    Session = sessionmaker(bind=engine)
    session = Session()

    portal = "data_gv_at"
    counts = []
    # list portal snapshots
    snapshots = get_portal_snapshots(session, portal)
    # list datasetscount
    for sn in snapshots:
        snapshot = sn['snapshot']
        print('snapshot: ' + str(snapshot))
        datasets = get_datasets(session, portalid=sn['portalid'], snapshot=snapshot)
        print('datasets: ' + str(len(datasets)))
        counts.append({'snapshot': str(snapshot), 'count': str(len(datasets))})

    with open(portal + '_snapshots.csv', 'w') as csvf:
        fieldnames = ['snapshot', 'count']
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(counts)


if __name__ == "__main__":
    start(sys.argv[1:])