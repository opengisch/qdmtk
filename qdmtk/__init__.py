# from . import settings as qdmtk_settings
import os
import tempfile

import django
from django.apps import apps
from django.conf import settings

from .exceptions import QDMTKException


def classFactory(iface):
    from .plugin import Plugin

    return Plugin(iface)


def register_datamodel(key, installed_apps, db_settings=None):
    """
    This configures the database connection and installed app django settings
    """
    if apps.ready:
        raise QDMTKException(
            "Only one datamodel can be registered simulatenously. If you are using multiple datamodels, you need to use separate user profiles."
        )

    # TODO : replace this by integrated GUI to configure the dataprovider
    # per datamodel key, ideally by selecting existing configs from the browser
    if db_settings is None:
        db_settings = {
            "ENGINE": "django.contrib.gis.db.backends.spatialite",
            "NAME": os.path.join(tempfile.gettempdir(), f"qdmtk_{key}.db"),
        }

    settings.configure(
        DATABASES={"default": db_settings},
        INSTALLED_APPS=installed_apps,
        # TODO : remove this and document setting through envvar
        # see https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/#ld-library-path-environment-variable
        GDAL_LIBRARY_PATH=r"C:\OSGeo4W\bin\gdal302.dll",
        GEOS_LIBRARY_PATH=r"C:\OSGeo4W\bin\geos_c.dll",
        SPATIALITE_LIBRARY_PATH=r"C:\OSGeo4W\bin\mod_spatialite.dll",
    )
    django.setup()
