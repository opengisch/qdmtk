from geoalchemy2.functions import functions
from qgis.core import (
    QgsAbstractFeatureIterator,
    QgsAbstractFeatureSource,
    QgsCoordinateTransform,
    QgsCsException,
    QgsDataProvider,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsFeatureIterator,
    QgsFeatureRequest,
    QgsGeometry,
    QgsMessageLog,
    QgsProject,
    QgsVectorDataProvider,
    QgsWkbTypes,
)

from .model.core import Base, Session


class FeatureIterator(QgsAbstractFeatureIterator):
    def __init__(self, source, request):
        QgsMessageLog.logMessage("FeatureIterator.__init__(...)", "debug_provider")
        super().__init__(request)
        self._request = request if request is not None else QgsFeatureRequest()
        self._source = source
        self._index = 0
        self._transform = QgsCoordinateTransform()
        if (
            self._request.destinationCrs().isValid()
            and self._request.destinationCrs() != self._source._provider.crs()
        ):
            self._transform = QgsCoordinateTransform(
                self._source._provider.crs(),
                self._request.destinationCrs(),
                self._request.transformContext(),
            )
        try:
            self._filter_rect = self.filterRectToSourceCrs(self._transform)
        except QgsCsException:
            self.close()
            return
        self._filter_rect = self.filterRectToSourceCrs(self._transform)
        if not self._filter_rect.isNull():
            self._select_rect_geom = QgsGeometry.fromRect(self._filter_rect)
            self._select_rect_engine = QgsGeometry.createGeometryEngine(
                self._select_rect_geom.constGet()
            )
            self._select_rect_engine.prepareGeometry()
        else:
            self._select_rect_engine = None
            self._select_rect_geom = None
        self._feature_id_list = None
        if (
            self._filter_rect is not None
            and self._source._provider._spatialindex is not None
        ):
            self._feature_id_list = self._source._provider._spatialindex.intersects(
                self._filter_rect
            )

        if (
            self._request.filterType() == QgsFeatureRequest.FilterFid
            or self._request.filterType() == QgsFeatureRequest.FilterFids
        ):
            fids = (
                [self._request.filterFid()]
                if self._request.filterType() == QgsFeatureRequest.FilterFid
                else self._request.filterFids()
            )
            self._feature_id_list = (
                list(set(self._feature_id_list).intersection(set(fids)))
                if self._feature_id_list
                else fids
            )

    def fetchFeature(self, f):
        """fetch next feature, return true on success"""
        QgsMessageLog.logMessage("FeatureIterator.fetchFeature(...)", "debug_provider")
        # virtual bool nextFeature( QgsFeature &f );
        if self._index < 0:
            f.setValid(False)
            return False
        try:
            found = False
            while not found:
                _f = self._source._features[
                    list(self._source._features.keys())[self._index]
                ]
                self._index += 1

                if (
                    self._feature_id_list is not None
                    and _f.id() not in self._feature_id_list
                ):
                    continue

                if not self._filter_rect.isNull():
                    if not _f.hasGeometry():
                        continue
                    if self._request.flags() & QgsFeatureRequest.ExactIntersect:
                        # do exact check in case we're doing intersection
                        if not self._select_rect_engine.intersects(
                            _f.geometry().constGet()
                        ):
                            continue
                    else:
                        if (
                            not _f.geometry()
                            .boundingBox()
                            .intersects(self._filter_rect)
                        ):
                            continue

                self._source._expression_context.setFeature(_f)
                if self._request.filterType() == QgsFeatureRequest.FilterExpression:
                    if not self._request.filterExpression().evaluate(
                        self._source._expression_context
                    ):
                        continue
                if self._source._subset_expression:
                    if not self._source._subset_expression.evaluate(
                        self._source._expression_context
                    ):
                        continue
                elif self._request.filterType() == QgsFeatureRequest.FilterFids:
                    if not _f.id() in self._request.filterFids():
                        continue
                elif self._request.filterType() == QgsFeatureRequest.FilterFid:
                    if _f.id() != self._request.filterFid():
                        continue
                f.setGeometry(_f.geometry())
                self.geometryToDestinationCrs(f, self._transform)
                f.setFields(_f.fields())
                f.setAttributes(_f.attributes())
                f.setValid(_f.isValid())
                f.setId(_f.id())
                return True
        except IndexError:
            f.setValid(False)
            return False

    def __iter__(self):
        """Returns self as an iterator object"""
        # QgsMessageLog.logMessage( "FeatureIterator.__iter__(...)","debug_provider")
        self._index = 0
        return self

    def __next__(self):
        """Returns the next value till current is lower than high"""
        # QgsMessageLog.logMessage( "FeatureIterator.__next__(...)","debug_provider")
        f = QgsFeature()
        if not self.nextFeature(f):
            raise StopIteration
        else:
            return f

    def rewind(self):
        """reset the iterator to the starting position"""
        QgsMessageLog.logMessage("FeatureIterator.rewind(...)", "debug_provider")
        # virtual bool rewind() = 0;
        if self._index < 0:
            return False
        self._index = 0
        return True

    def close(self):
        """end of iterating: free the resources / lock"""
        QgsMessageLog.logMessage("FeatureIterator.close(...)", "debug_provider")
        # virtual bool close() = 0;
        self._index = -1
        return True


class FeatureSource(QgsAbstractFeatureSource):
    def __init__(self, provider):
        QgsMessageLog.logMessage("FeatureSource.__init__(...)", "debug_provider")
        super(FeatureSource, self).__init__()
        self.provider = provider
        self._features = provider._features

        self._expression_context = QgsExpressionContext()
        self._expression_context.appendScope(QgsExpressionContextUtils.globalScope())
        self._expression_context.appendScope(
            QgsExpressionContextUtils.projectScope(QgsProject.instance())
        )
        self._expression_context.setFields(self._provider.fields())
        if self._provider.subsetString():
            self._subset_expression = QgsExpression(self._provider.subsetString())
            self._subset_expression.prepare(self._expression_context)
        else:
            self._subset_expression = None

    def getFeatures(self, request):
        QgsMessageLog.logMessage("FeatureSource.getFeatures(...)", "debug_provider")
        session = Session()
        session.query(self.provider.model)
        return QgsFeatureIterator(FeatureIterator(self, request))


class Provider(QgsVectorDataProvider):

    next_feature_id = 1

    @classmethod
    def providerKey(cls):
        """Returns the memory provider key"""
        QgsMessageLog.logMessage("Provider.providerKey(...)", "debug_provider")
        return "qdatamodel_provider"

    @classmethod
    def description(cls):
        """Returns the memory provider description"""
        QgsMessageLog.logMessage("Provider.description(...)", "debug_provider")
        return "QDatamodel Provider"

    @classmethod
    def createProvider(cls, uri, providerOptions, flags=QgsDataProvider.ReadFlags()):
        QgsMessageLog.logMessage("Provider.createProvider(...)", "debug_provider")
        return Provider(uri, providerOptions, flags)

    # Implementation of functions from QgsVectorDataProvider

    def __init__(
        self,
        uri="",
        providerOptions=QgsDataProvider.ProviderOptions(),
        flags=QgsDataProvider.ReadFlags(),
    ):
        super().__init__(uri)
        QgsMessageLog.logMessage("Provider.__init__(...)", "debug_provider")

        self.uri = uri
        self.model = getattr(Base, self.uri)

    def featureSource(self):
        QgsMessageLog.logMessage("Provider.featureSource(...)", "debug_provider")
        return FeatureSource(self)

    def dataSourceUri(self, expandAuthConfig=True):
        QgsMessageLog.logMessage("Provider.dataSourceUri(...)", "debug_provider")
        return self.uri

    def storageType(self):
        QgsMessageLog.logMessage("Provider.storageType(...)", "debug_provider")
        return self.providerKey()

    def getFeatures(self, request=QgsFeatureRequest()):
        QgsMessageLog.logMessage("Provider.getFeatures(...)", "debug_provider")
        return QgsFeatureIterator(FeatureIterator(FeatureSource(self), request))

    def uniqueValues(self, fieldIndex, limit=1):
        QgsMessageLog.logMessage("Provider.uniqueValues(...)", "debug_provider")
        results = set()
        if fieldIndex >= 0 and fieldIndex < self.fields().count():
            req = QgsFeatureRequest()
            req.setFlags(QgsFeatureRequest.NoGeometry)
            req.setSubsetOfAttributes([fieldIndex])
            for f in self.getFeatures(req):
                results.add(f.attributes()[fieldIndex])
        return results

    def wkbType(self):
        QgsMessageLog.logMessage("Provider.wkbType(...)", "debug_provider")
        return QgsWkbTypes.parseType(self.model.geom.geometry_type)

    def featureCount(self):
        QgsMessageLog.logMessage("Provider.featureCount(...)", "debug_provider")
        session = Session()
        return session.select(self.model).count()

    def fields(self):
        QgsMessageLog.logMessage("Provider.fields(...)", "debug_provider")
        return self._fields

    def addFeatures(self, flist, flags=None):
        QgsMessageLog.logMessage("Provider.addFeatures(...)", "debug_provider")
        session = Session()
        for f in flist:
            row = self.model()
            # TODO : copy geom and attributes to row
            session.add(row)
        session.commit()

    def deleteFeatures(self, ids):
        QgsMessageLog.logMessage("Provider.deleteFeatures(...)", "debug_provider")
        session = Session()
        # TODO synchronize_session=True if we use transaction
        session.query(self.model).filter(self.model.id.in_(ids)).delete(
            synchronize_session=False
        )
        session.commit()

    def changeAttributeValues(self, attr_map):
        QgsMessageLog.logMessage(
            "Provider.changeAttributeValues(...)", "debug_provider"
        )
        session = Session()
        for feature_id, attrs in attr_map.items():
            row = session.query(self.model).get(feature_id)
            for k, v in attrs.items():
                setattr(row, k, v)
        session.commit()
        return True

    def changeGeometryValues(self, geometry_map):
        QgsMessageLog.logMessage("Provider.changeGeometryValues(...)", "debug_provider")
        session = Session()
        for feature_id, geometry in geometry_map.items():
            row = session.query(self.model).get(feature_id)
            row.geom = geometry  # probably need to parse/cast somehow
        session.commit()
        return True

    def allFeatureIds(self):
        QgsMessageLog.logMessage("Provider.allFeatureIds(...)", "debug_provider")
        session = Session()
        return session.query(self.model.id).all()

    def subsetString(self):
        QgsMessageLog.logMessage("Provider.subsetString(...)", "debug_provider")
        return ""

    def setSubsetString(self, subsetString):
        QgsMessageLog.logMessage("Provider.setSubsetString(...)", "debug_provider")
        raise NotImplementedError()

    def supportsSubsetString(self):
        QgsMessageLog.logMessage("Provider.supportsSubsetString(...)", "debug_provider")
        return False

    def capabilities(self):
        QgsMessageLog.logMessage("Provider.capabilities(...)", "debug_provider")
        return (
            QgsVectorDataProvider.AddFeatures
            | QgsVectorDataProvider.DeleteFeatures
            | QgsVectorDataProvider.ChangeGeometries
            | QgsVectorDataProvider.ChangeAttributeValues
            | QgsVectorDataProvider.SelectAtId
        )

    # /* Implementation of functions from QgsDataProvider */

    def name(self):
        QgsMessageLog.logMessage("Provider.name(...)", "debug_provider")
        return self.providerKey()

    def extent(self):
        QgsMessageLog.logMessage("Provider.extent(...)", "debug_provider")
        return self._extent

    def updateExtents(self):
        QgsMessageLog.logMessage("Provider.updateExtents(...)", "debug_provider")
        session = Session()
        self._extent = session.query(
            functions.extent(self.model.geom)
        )  # TODO cast to QgsRectangle

    def isValid(self):
        QgsMessageLog.logMessage("Provider.isValid(...)", "debug_provider")
        return True

    def crs(self):
        QgsMessageLog.logMessage("Provider.crs(...)", "debug_provider")
        return self.model.geom.srid

    def handlePostCloneOperations(self, source):
        QgsMessageLog.logMessage(
            "Provider.handlePostCloneOperations(...)", "debug_provider"
        )
