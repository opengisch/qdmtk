import os
import tempfile

# DEBUG=True

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": os.path.join(tempfile.gettempdir(), "qdatamodel.db"),
    }
}

INSTALLED_APPS = [
    "qdatamodel.model.core",
]


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECRET_KEY = "REPLACE_ME"

GDAL_LIBRARY_PATH = r"C:\OSGeo4W\bin\gdal302.dll"
GEOS_LIBRARY_PATH = r"C:\OSGeo4W\bin\geos_c.dll"
SPATIALITE_LIBRARY_PATH = r"C:\OSGeo4W\bin\mod_spatialite.dll"
