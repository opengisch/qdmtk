"""
Adapted from example in https://github.com/qgis/QGIS/blob/master/tests/src/python/provider_python.py

"""

from geoalchemy2.functions import ST_Collect, ST_GeomFromText, ST_Intersects
from qgis.core import (
    NULL,
    QgsAbstractFeatureIterator,
    QgsAbstractFeatureSource,
    QgsCoordinateReferenceSystem,
    QgsDataProvider,
    QgsFeatureIterator,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsMessageLog,
    QgsRectangle,
    QgsVectorDataProvider,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant
from sqlalchemy import inspect, types

from .model import core
from .model.core import Session
from .utils import MaxX, MaxY, MinX, MinY


class FeatureIterator(QgsAbstractFeatureIterator):
    def __init__(self, source, request):
        super().__init__(request)
        self.request = request
        self.source = source

        self.rewind()

    def fetchFeature(self, f):
        """fetch next feature, return true on success"""
        try:
            row = next(self.iterator)

            # Geometry
            geom = QgsGeometry()
            if row.geom is not None:
                geom.fromWkb(row.geom.data)
            f.setGeometry(geom)
            # self.geometryToDestinationCrs(f, self._transform)

            # Fields
            f.setFields(self.source.provider.fields())
            for attr in self.source.provider._attrs():
                f.setAttribute(attr.key, getattr(row, attr.key))

            f.setValid(True)
            f.setId(row.id)
            return True
        except StopIteration:
            f.setValid(False)
            return False

    def __iter__(self):
        """Returns self as an iterator object"""
        return self

    def __next__(self):
        """Returns the next value till current is lower than high"""
        return next(self.iterator)

    def rewind(self):
        """reset the iterator to the starting position"""
        self.session = Session()

        query = self.session.query(self.source.provider.model)

        filter_rect = self.request.filterRect()
        if not filter_rect.isNull():
            # TODO : probably need to transform rect CRS if needed like this
            # transform = QgsCoordinateTransform()
            # if self.request.destinationCrs().isValid() and self.request.destinationCrs() != self.source.provider.crs():
            #     transform = QgsCoordinateTransform(self.source.provider.crs(), self.request.destinationCrs(), self.request.transformContext())

            query = query.filter(
                ST_Intersects(
                    ST_GeomFromText(filter_rect.asWktPolygon()),
                    self.source.provider.model.geom,
                )
            )

        # TODO : implement rest of filter, such as order_by, select by id, etc. (and expression ?)

        self.iterator = iter(query.all())
        self.session.close()
        return True

    def close(self):
        """end of iterating: free the resources / lock"""
        self.iterator = None
        self.session.close()
        return True


class FeatureSource(QgsAbstractFeatureSource):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def getFeatures(self, request):
        return QgsFeatureIterator(FeatureIterator(self, request))


class Provider(QgsVectorDataProvider):
    @classmethod
    def providerKey(cls):
        """Returns the memory provider key"""
        return "qdatamodel_provider"

    @classmethod
    def description(cls):
        """Returns the memory provider description"""
        return "QDatamodel Provider"

    @classmethod
    def createProvider(cls, uri, providerOptions, flags=QgsDataProvider.ReadFlags()):
        return Provider(uri, providerOptions, flags)

    # Implementation of functions from QgsVectorDataProvider

    def __init__(
        self,
        uri="",
        providerOptions=QgsDataProvider.ProviderOptions(),
        flags=QgsDataProvider.ReadFlags(),
    ):
        super().__init__(uri)

        self.uri = uri
        self.model = getattr(core, self.uri)
        self._extent = None

    def featureSource(self):
        return FeatureSource(self)

    def dataSourceUri(self, expandAuthConfig=True):
        return self.uri

    def storageType(self):
        return self.providerKey()

    def getFeatures(self, request=QgsFeatureRequest()):
        return self.featureSource().getFeatures(request)

    def uniqueValues(self, fieldIndex, limit=1):
        field = self._attrs_map()[fieldIndex]
        session = Session()
        return [r[0] for r in session.query(getattr(self.model, field)).distinct()]

    def wkbType(self):
        return QgsWkbTypes.parseType(
            inspect(self.model.geom).expression.type.geometry_type
        )

    def featureCount(self):
        session = Session()
        return session.query(self.model).count()

    def _attrs(self):
        """
        Yields SQLAlchemy's attributes (non-geom)
        """
        for field in inspect(self.model).attrs:
            if field.key == "geom":
                continue
            yield field

    def _attrs_map(self) -> "dict[int, str]":
        """
        Returns a dict that maps field idx to field name
        """
        return {i: attr.key for i, attr in enumerate(self._attrs())}

    def fields(self):
        fields = QgsFields()
        for attr in self._attrs():
            if isinstance(attr.expression.type, types.String):
                type_ = QVariant.String
            elif isinstance(attr.expression.type, types.Integer):
                type_ = QVariant.Int
            elif isinstance(attr.expression.type, types.Float) or isinstance(
                attr.expression.type, types.Numeric
            ):
                type_ = QVariant.Double
            else:
                QgsMessageLog.logMessage(
                    f"Field type not configured : {attr.expression.type.__class__.__name__} ({attr.key} [{attr.expression.type}])",
                )
                type_ = QVariant.Invalid
            fields.append(QgsField(attr.key, type_))
        return fields

    def addFeatures(self, flist, flags=None):
        session = Session()
        for f in flist:
            row = self.model()
            # row.geom = f.geometry().asWkb()  # doesn't work...
            row.geom = ST_GeomFromText(f.geometry().asWkt(), 4326)
            for attr in self._attrs():
                value = f.attribute(attr.key)
                if value == NULL:
                    value = None
                setattr(row, attr.key, value)
            session.add(row)
        session.commit()
        return True, flist

    def deleteFeatures(self, ids):
        session = Session()
        # TODO synchronize_session=True if we use transaction
        session.query(self.model).filter(self.model.id.in_(ids)).delete(
            synchronize_session=False
        )
        session.commit()

    def changeAttributeValues(self, attr_map):
        attrs_map = self._attrs_map()
        session = Session()
        for fid, attrs in attr_map.items():
            row = session.query(self.model).get(fid)
            for k, v in attrs.items():
                setattr(row, attrs_map[k], v)
        session.commit()
        return True

    def changeGeometryValues(self, geometry_map):
        session = Session()
        for feature_id, geometry in geometry_map.items():
            row = session.query(self.model).get(feature_id)
            # row.geom = geometry.asWkb()  # doesn't work...
            row.geom = ST_GeomFromText(geometry.asWkt(), 4326)
        session.commit()
        return True

    def allFeatureIds(self):
        session = Session()
        return session.query(self.model.id).all()

    def subsetString(self):
        return ""

    def setSubsetString(self, subsetString):
        raise NotImplementedError()

    def supportsSubsetString(self):
        return False

    def capabilities(self):
        return (
            QgsVectorDataProvider.AddFeatures
            | QgsVectorDataProvider.DeleteFeatures
            | QgsVectorDataProvider.ChangeGeometries
            | QgsVectorDataProvider.ChangeAttributeValues
            | QgsVectorDataProvider.SelectAtId
        )

    # /* Implementation of functions from QgsDataProvider */

    def name(self):
        return self.providerKey()

    def extent(self):
        if self._extent is None:
            self.updateExtents()
        return self._extent

    def updateExtents(self):
        session = Session()
        geoms = ST_Collect(self.model.geom)
        extents = session.query(
            MinX(geoms), MinY(geoms), MaxX(geoms), MaxY(geoms)
        ).one()
        self._extent = QgsRectangle(
            extents[0] or 0, extents[1] or 0, extents[2] or 0, extents[3] or 0
        )

    def isValid(self):
        return True

    def crs(self):
        crs = QgsCoordinateReferenceSystem()
        srid = inspect(self.model.geom).expression.type.srid
        crs.createFromString(f"EPSG:{srid}")
        return crs

    def handlePostCloneOperations(self, source):
        pass
