
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()



class Portal(Base):
    __tablename__ = tab_portals

    id      = Column(String, primary_key=True, index=True,nullable=False)
    uri     = Column(String, nullable=False)
    apiuri  = Column(String)
    software = Column(String(12), nullable=False) # OpenDataSoft, CKAN, Socrata <13
    iso     = Column(String(2), nullable=False)
    active  = Column(Boolean, default=True,nullable=False)


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


class Dataset(Base):
    __tablename__ = tab_datasets

    id           = Column( String, primary_key=True)
    snapshot     = Column( SmallInteger, primary_key=True, index=True)
    portalid     = Column( String, primary_key=True, index=True)
    organisation = Column(String, index=True)
    title        = Column(String, index=True)
    md5          = Column(String, ForeignKey(tab_datasetsdata+'.md5'), index=True)


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


def get_portal_snapshots(portalid):
    with db.begin_session() as s:
        q = s.query(PortalSnapshot)
        q = q.filter(PortalSnapshot.portalid == portalid) \
            .outerjoin(PortalSnapshotQuality, and_(PortalSnapshot.portalid == PortalSnapshotQuality.portalid,
                                                   PortalSnapshot.snapshot == PortalSnapshotQuality.snapshot)) \
            .join(Portal) \
            .add_entity(PortalSnapshotQuality) \
            .add_entity(Portal)
        return jsonify([row2dict(i) for i in q.all()])

def get_datasets(portalid, datasetid, snapshot):
    with db.begin_session() as s:
        q = s.query(DatasetData) \
            .join(Dataset, DatasetData.md5 == Dataset.md5) \
            .filter(Dataset.snapshot == snapshot) \
            .filter(Dataset.portalid == portalid) \
            .filter(Dataset.id == datasetid)
        data = [row2dict(r) for r in q.all()]

