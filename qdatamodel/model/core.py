from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Structure(Base):
    __tablename__ = "structures"
    id = Column(Integer, primary_key=True)
    geom = Column(Geometry("POINT", srid=4326, management=True))
    name = Column(String)


class Building(Structure):
    __tablename__ = "buildings"
    id = Column(Integer, ForeignKey("structures.id"), primary_key=True)
    stories_count = Column(Integer)


engine = create_engine("sqlite:///:memory:")


def load_spatialite(dbapi_conn, connection_record):
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.execute('SELECT load_extension("mod_spatialite")')
    dbapi_conn.execute("SELECT InitSpatialMetaData(1)")


listen(engine, "connect", load_spatialite)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

session = Session()
session.add(
    Building(name="my house", stories_count=4, geom="SRID=4326;POINT(6.14 46.20)")
)
session.add(Structure(name="your house", geom="SRID=4326;POINT(6.16 46.21)"))
session.commit()
session.close()
