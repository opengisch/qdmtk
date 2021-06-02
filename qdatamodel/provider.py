"""
Adapted from example in https://github.com/qgis/QGIS/blob/master/tests/src/python/provider_python.py

"""

import django
import django.conf
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import GEOSGeometry
from django.db import models
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
                geom.fromWkb(row.geom.wkb.tobytes())
            f.setGeometry(geom)
            # self.geometryToDestinationCrs(f, self._transform)

            # Fields
            f.setFields(self.source.provider.fields())
            for attr in self.source.provider._attrs():
                f.setAttribute(attr.name, getattr(row, attr.name))

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

        query = self.source.provider.model.objects

        filter_rect = self.request.filterRect()
        if not filter_rect.isNull():
            # TODO : probably need to transform rect CRS if needed like this
            # transform = QgsCoordinateTransform()
            # if self.request.destinationCrs().isValid() and self.request.destinationCrs() != self.source.provider.crs():
            #     transform = QgsCoordinateTransform(self.source.provider.crs(), self.request.destinationCrs(), self.request.transformContext())
            query = query.filter(
                geom__bboverlaps=GEOSGeometry(filter_rect.asWktPolygon())
            )

        # TODO : implement rest of filter, such as order_by, select by id, etc. (and expression ?)

        self.iterator = iter(query.all())
        return True

    def close(self):
        """end of iterating: free the resources / lock"""
        self.iterator = None
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

        for model in django.apps.apps.get_models():
            if model.__name__ == self.uri:
                self.model = model
                break
        else:
            known_models = [model.__name__ for model in django.apps.apps.get_models()]
            raise Exception(
                f"Could not find model {self.uri}. Known models are {known_models}"
            )

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
        return self.model.objects.values_list(field, flat=True).distinct()

    def wkbType(self):
        return QgsWkbTypes.parseType(self.model.geom.field.geom_type)

    def featureCount(self):
        return self.model.objects.count()

    def _attrs(self):
        """
        Yields SQLAlchemy's attributes (non-geom)
        """
        for field in self.model._meta.get_fields():
            if isinstance(field, (models.OneToOneField, models.ManyToOneRel)):
                # Skip non-field attributes
                continue
            if field.name == "geom":
                continue
            yield field

    def _attrs_map(self) -> "dict[int, str]":
        """
        Returns a dict that maps field idx to field name
        """
        return {i: attr.name for i, attr in enumerate(self._attrs())}

    def fields(self):
        fields = QgsFields()
        for attr in self._attrs():
            if isinstance(attr, models.TextField) or isinstance(attr, models.CharField):
                type_ = QVariant.String
            elif isinstance(attr, models.IntegerField):
                type_ = QVariant.Int
            elif isinstance(attr, models.FloatField) or isinstance(
                attr, models.DecimalField
            ):
                type_ = QVariant.Double
            else:
                QgsMessageLog.logMessage(
                    f"Field type not configured : {attr.__class__.__name__} ({attr.name})",
                )
                type_ = QVariant.Invalid
            fields.append(QgsField(attr.name, type_))
        return fields

    def addFeatures(self, flist, flags=None):
        for f in flist:
            instance = self.model()
            instance.geom = GEOSGeometry(f.geometry().asWkt())
            for attr in self._attrs():
                value = f.attribute(attr.name)
                setattr(instance, attr.name, value if value != NULL else None)
            instance.save()
        return True, flist

    def deleteFeatures(self, ids):
        for instance in self.model.objects.filter(id__in=ids):
            instance.delete()

    def changeAttributeValues(self, attr_map):
        attrs_map = self._attrs_map()
        for fid, attrs in attr_map.items():
            instance = self.model.objects.get(id=fid)
            for k, value in attrs.items():
                setattr(instance, attrs_map[k], value if value != NULL else None)
            instance.save()
        return True

    def changeGeometryValues(self, geometry_map):
        for fid, geometry in geometry_map.items():
            instance = self.model.objects.get(id=fid)
            instance.geom = GEOSGeometry(geometry.asWkt())
            instance.save()
        return True

    def allFeatureIds(self):
        return self.model.objects.values_list("id", flat=True)

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
        extents = self.model.objects.aggregate(extent=Extent("geom"))["extent"]
        if extents:
            self._extent = QgsRectangle(extents[0], extents[1], extents[2], extents[3])
        else:
            self._extent = QgsRectangle()

    def isValid(self):
        return True

    def crs(self):
        crs = QgsCoordinateReferenceSystem()
        srid = self.model.geom.field.srid
        crs.createFromString(f"EPSG:{srid}")
        return crs

    def handlePostCloneOperations(self, source):
        pass
