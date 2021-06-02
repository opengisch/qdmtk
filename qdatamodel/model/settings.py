import os
import tempfile

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": os.path.join(tempfile.gettempdir(), "qdatamodel.db"),
    }
}

INSTALLED_APPS = [
    "qdatamodel.model.core",
]

GDAL_LIBRARY_PATH = r"C:\OSGeo4W\bin\gdal302.dll"
GEOS_LIBRARY_PATH = r"C:\OSGeo4W\bin\geos_c.dll"
SPATIALITE_LIBRARY_PATH = r"C:\OSGeo4W\bin\mod_spatialite.dll"
