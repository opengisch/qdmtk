import os
import tempfile

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import column_property, declarative_base, sessionmaker
from sqlalchemy.sql.expression import cast

from ..utils import NonExtendedGeometry

Base = declarative_base()


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
    dbapi_conn.execute('SELECT load_extension("mod_spatialite")')
    dbapi_conn.execute("SELECT InitSpatialMetaData(1)")


listen(engine, "connect", load_spatialite)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

# Initial data
session = Session()
if session.query(Building).count() == 0:
    session.add(
        Building(
            name="my house",
            stories_count=4,
            geom="SRID=4326;POINT(6.14 46.20)",
        )
    )
    session.add(
        Structure(
            name="your house",
            geom="SRID=4326;POINT(6.16 46.21)",
        )
    )
    session.commit()
session.close()
