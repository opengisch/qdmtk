from geoalchemy2.types import Geometry
from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.types import Numeric


class NonExtendedGeometry(Geometry):
    """
    GeoAlchemy2's Geometry use EWKB by default, preventing us from using QgsGeometry.fromWkb
    directly. Thiss ubclass uses WKB instead
    """

    as_binary = "ST_AsBinary"


class Extent(GenericFunction):
    type = Geometry
    package = "geo"
    name = "Extent"  # ST_Extent on Postgis
    identifier = "buffer"


class MinX(GenericFunction):
    type = Numeric
    package = "geo"
    name = "MbrMinX"  # ST_XMin on Postgis
    identifier = "buffer"


class MaxX(GenericFunction):
    type = Numeric
    package = "geo"
    name = "MbrMaxX"  # ST_XMax on Postgis
    identifier = "buffer"


class MinY(GenericFunction):
    type = Numeric
    package = "geo"
    name = "MbrMinY"  # ST_YMin on Postgis
    identifier = "buffer"


class MaxY(GenericFunction):
    type = Numeric
    package = "geo"
    name = "MbrMaxY"  # ST_YMax on Postgis
    identifier = "buffer"
