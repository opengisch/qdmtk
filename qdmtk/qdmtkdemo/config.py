import os
import tempfile

DATAMODEL_NAME = "qdmtkdemo"
DATABASE = {
    "ENGINE": "django.contrib.gis.db.backends.spatialite",
    "NAME": os.path.join(tempfile.gettempdir(), f"qdmtkdemo.db"),
}
INSTALLED_APPS = ["qdmtk.qdmtkdemo"]
