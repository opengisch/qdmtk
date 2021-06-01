import os
import tempfile

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import column_property, declarative_base
from sqlalchemy.sql.expression import cast

from ..utils import NonExtendedGeometry

Base = declarative_base()

# sys.path.insert(0, r'C:\OSGeo4W\bin')
# os.environ['PATH'] = r'C:\OSGeo4W\bin;' + os.environ['PATH']


class Structure(Base):
    __tablename__ = "structures"
    id = Column(Integer, primary_key=True)
    geom = Column(NonExtendedGeometry("POINT", srid=4326, management=True))
    name = Column(String)
    label = column_property(name + "(" + cast(id, String) + ")")


class Building(Structure):
    __tablename__ = "buildings"
    id = Column(Integer, ForeignKey("structures.id"), primary_key=True)
    stories_count = Column(Integer)


class Monument(Structure):
    __tablename__ = "monuments"
    id = Column(Integer, ForeignKey("structures.id"), primary_key=True)
    tripadvisor_rating = Column(Integer)


db_path = os.path.join(tempfile.gettempdir(), "qdatamodel.db")
engine = create_engine(f"sqlite:///{db_path}", echo=False)


def load_spatialite(dbapi_conn, connection_record):
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.execute("SELECT load_extension('mod_spatialite')")
    dbapi_conn.execute("SELECT InitSpatialMetaData(1)")


listen(engine, "connect", load_spatialite)

# Base.metadata.create_all(engine)
