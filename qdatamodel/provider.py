from geoalchemy2.functions import ST_Collect
from qgis.core import (
    QgsAbstractFeatureIterator,
    QgsAbstractFeatureSource,
    QgsCoordinateReferenceSystem,
    QgsDataProvider,
    QgsFeatureIterator,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsMessageLog,
    QgsRectangle,
    QgsVectorDataProvider,
    QgsWkbTypes,
)
from sqlalchemy import inspect

from .model import core
from .model.core import Session
from .utils import MaxX, MaxY, MinX, MinY


class FeatureIterator(QgsAbstractFeatureIterator):
    def __init__(self, source, request):
        # QgsMessageLog.logMessage("FeatureIterator.__init__(...)", "debug_provider")
        super().__init__(request)
        self.request = request if request is not None else QgsFeatureRequest()
        self.source = source

        self.rewind()

    def fetchFeature(self, f):
        """fetch next feature, return true on success"""
        # QgsMessageLog.logMessage("FeatureIterator.fetchFeature(...)", "debug_provider")
        try:
            row = next(self.iterator)
            f.setGeometry(row.geom)
            # self.geometryToDestinationCrs(f, self._transform)
            f.setFields(self.source.provider.fields())
            f.setAttributes(row.__dict__())
            f.setValid(True)
            f.setId(row.id)
            return True
        except StopIteration:
            f.setValid(False)
            return False

    def __iter__(self):
        """Returns self as an iterator object"""
        QgsMessageLog.logMessage("FeatureIterator.__iter__(...)", "debug_provider")
        return self

    def __next__(self):
        """Returns the next value till current is lower than high"""
        QgsMessageLog.logMessage("FeatureIterator.__next__(...)", "debug_provider")
        return next(self.iterator)

    def rewind(self):
        """reset the iterator to the starting position"""
        # QgsMessageLog.logMessage("FeatureIterator.rewind(...)", "debug_provider")
        self.session = Session()
        # self.iterator = iter(self.session.query(self.source.provider.model).all())
        self.iterator = iter([])
        return True

    def close(self):
        """end of iterating: free the resources / lock"""
        # QgsMessageLog.logMessage("FeatureIterator.close(...)", "debug_provider")
        self.iterator = None
        self.session.close()
        return True


class FeatureSource(QgsAbstractFeatureSource):
    def __init__(self, provider):
        # QgsMessageLog.logMessage("FeatureSource.__init__(...)", "debug_provider")
        super(FeatureSource, self).__init__()
        self.provider = provider

    def getFeatures(self, request):
        # QgsMessageLog.logMessage("FeatureSource.getFeatures(...)", "debug_provider")
        session = Session()
        session.query(self.provider.model)
        return QgsFeatureIterator(FeatureIterator(self, request))


class Provider(QgsVectorDataProvider):

    next_feature_id = 1

    @classmethod
    def providerKey(cls):
        """Returns the memory provider key"""
        # QgsMessageLog.logMessage("Provider.providerKey(...)", "debug_provider")
        return "qdatamodel_provider"

    @classmethod
    def description(cls):
        """Returns the memory provider description"""
        # QgsMessageLog.logMessage("Provider.description(...)", "debug_provider")
        return "QDatamodel Provider"

    @classmethod
    def createProvider(cls, uri, providerOptions, flags=QgsDataProvider.ReadFlags()):
        # QgsMessageLog.logMessage("Provider.createProvider(...)", "debug_provider")
        return Provider(uri, providerOptions, flags)

    # Implementation of functions from QgsVectorDataProvider

    def __init__(
        self,
        uri="",
        providerOptions=QgsDataProvider.ProviderOptions(),
        flags=QgsDataProvider.ReadFlags(),
    ):
        QgsMessageLog.logMessage("Provider.__init__(...)", "debug_provider")
        super().__init__(uri)

        self.uri = uri
        self.model = getattr(core, self.uri)
        self._extent = None

    def featureSource(self):
        # QgsMessageLog.logMessage("Provider.featureSource(...)", "debug_provider")
        return FeatureSource(self)

    def dataSourceUri(self, expandAuthConfig=True):
        # QgsMessageLog.logMessage("Provider.dataSourceUri(...)", "debug_provider")
        return self.uri

    def storageType(self):
        # QgsMessageLog.logMessage("Provider.storageType(...)", "debug_provider")
        return self.providerKey()

    def getFeatures(self, request=QgsFeatureRequest()):
        # QgsMessageLog.logMessage("Provider.getFeatures(...)", "debug_provider")
        return QgsFeatureIterator(FeatureIterator(FeatureSource(self), request))

    def uniqueValues(self, fieldIndex, limit=1):
        # QgsMessageLog.logMessage("Provider.uniqueValues(...)", "debug_provider")
        results = set()
        if fieldIndex >= 0 and fieldIndex < self.fields().count():
            req = QgsFeatureRequest()
            req.setFlags(QgsFeatureRequest.NoGeometry)
            req.setSubsetOfAttributes([fieldIndex])
            for f in self.getFeatures(req):
                results.add(f.attributes()[fieldIndex])
        return results

    def wkbType(self):
        # QgsMessageLog.logMessage("Provider.wkbType(...)", "debug_provider")
        return QgsWkbTypes.parseType(
            inspect(self.model.geom).expression.type.geometry_type
        )

    def featureCount(self):
        # QgsMessageLog.logMessage("Provider.featureCount(...)", "debug_provider")
        session = Session()
        return session.query(self.model).count()

    def fields(self):
        # QgsMessageLog.logMessage("Provider.fields(...)", "debug_provider")
        mapper = inspect(self.model)
        fields = QgsFields()
        for column in mapper.attrs:
            fields.append(QgsField(column.key))
        return fields

    def addFeatures(self, flist, flags=None):
        # QgsMessageLog.logMessage("Provider.addFeatures(...)", "debug_provider")
        session = Session()
        for f in flist:
            row = self.model()
            # TODO : copy geom and attributes to row
            session.add(row)
        session.commit()

    def deleteFeatures(self, ids):
        # QgsMessageLog.logMessage("Provider.deleteFeatures(...)", "debug_provider")
        session = Session()
        # TODO synchronize_session=True if we use transaction
        session.query(self.model).filter(self.model.id.in_(ids)).delete(
            synchronize_session=False
        )
        session.commit()

    def changeAttributeValues(self, attr_map):
        # QgsMessageLog.logMessage("Provider.changeAttributeValues(...)", "debug_provider")
        session = Session()
        for feature_id, attrs in attr_map.items():
            row = session.query(self.model).get(feature_id)
            for k, v in attrs.items():
                setattr(row, k, v)
        session.commit()
        return True

    def changeGeometryValues(self, geometry_map):
        # QgsMessageLog.logMessage("Provider.changeGeometryValues(...)", "debug_provider")
        session = Session()
        for feature_id, geometry in geometry_map.items():
            row = session.query(self.model).get(feature_id)
            row.geom = geometry  # probably need to parse/cast somehow
        session.commit()
        return True

    def allFeatureIds(self):
        # QgsMessageLog.logMessage("Provider.allFeatureIds(...)", "debug_provider")
        session = Session()
        return session.query(self.model.id).all()

    def subsetString(self):
        # QgsMessageLog.logMessage("Provider.subsetString(...)", "debug_provider")
        return ""

    def setSubsetString(self, subsetString):
        # QgsMessageLog.logMessage("Provider.setSubsetString(...)", "debug_provider")
        raise NotImplementedError()

    def supportsSubsetString(self):
        # QgsMessageLog.logMessage("Provider.supportsSubsetString(...)", "debug_provider")
        return False

    def capabilities(self):
        # QgsMessageLog.logMessage("Provider.capabilities(...)", "debug_provider")
        return (
            QgsVectorDataProvider.AddFeatures
            | QgsVectorDataProvider.DeleteFeatures
            | QgsVectorDataProvider.ChangeGeometries
            | QgsVectorDataProvider.ChangeAttributeValues
            | QgsVectorDataProvider.SelectAtId
        )

    # /* Implementation of functions from QgsDataProvider */

    def name(self):
        # QgsMessageLog.logMessage("Provider.name(...)", "debug_provider")
        return self.providerKey()

    def extent(self):
        # QgsMessageLog.logMessage("Provider.extent(...)", "debug_provider")
        if self._extent is None:
            self.updateExtents()
        return self._extent

    def updateExtents(self):
        # QgsMessageLog.logMessage("Provider.updateExtents(...)", "debug_provider")
        session = Session()
        geoms = ST_Collect(self.model.geom)
        extents = session.query(
            MinX(geoms), MinY(geoms), MaxX(geoms), MaxY(geoms)
        ).one()
        self._extent = QgsRectangle(extents[0], extents[1], extents[2], extents[3])

    def isValid(self):
        QgsMessageLog.logMessage("Provider.isValid(...)", "debug_provider")
        return True

    def crs(self):
        # QgsMessageLog.logMessage("Provider.crs(...)", "debug_provider")
        crs = QgsCoordinateReferenceSystem()
        srid = inspect(self.model.geom).expression.type.srid
        crs.createFromString(f"EPSG:{srid}")
        return crs

    def handlePostCloneOperations(self, source):
        # QgsMessageLog.logMessage("Provider.handlePostCloneOperations(...)", "debug_provider")
        pass
