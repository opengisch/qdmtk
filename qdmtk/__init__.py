# from . import settings as qdmtk_settings
import os
import tempfile

from .version import __version__  # noqa


def classFactory(iface):
    from .plugin import Plugin

    return Plugin(iface)


def register_datamodel(key, installed_apps, db_settings=None):
    """
    This configures the database connection and installed app django settings
    """
    import django
    from django.apps import apps
    from django.conf import settings

    from .exceptions import QDMTKException

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

    # Allow to configure GDAL/GEOS/Spatialite libraries from env vars
    # see https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/geolibs/#geos-library-path
    GDAL_LIBRARY_PATH_ENV = os.getenv("GDAL_LIBRARY_PATH")
    GEOS_LIBRARY_PATH_ENV = os.getenv("GEOS_LIBRARY_PATH")
    SPATIALITE_LIBRARY_PATH_ENV = os.getenv("SPATIALITE_LIBRARY_PATH")
    additionnal_settings = {}
    if GDAL_LIBRARY_PATH_ENV:
        additionnal_settings["GDAL_LIBRARY_PATH"] = GDAL_LIBRARY_PATH_ENV
    if GEOS_LIBRARY_PATH_ENV:
        additionnal_settings["GEOS_LIBRARY_PATH"] = GEOS_LIBRARY_PATH_ENV
    if SPATIALITE_LIBRARY_PATH_ENV:
        additionnal_settings["SPATIALITE_LIBRARY_PATH"] = SPATIALITE_LIBRARY_PATH_ENV

    settings.configure(
        DATABASES={"default": db_settings},
        INSTALLED_APPS=installed_apps,
        **additionnal_settings,
    )
    django.setup()
