import os

from .version import __version__  # noqa

# This will hold all registered datamodels
datamodels_registry = {}


def classFactory(iface):
    from .plugin import Plugin

    return Plugin(iface)


def register_datamodel(datamodel_key, installed_apps, db_settings):
    """
    This registers the database connection and installed apps for the given datamodel.
    These will be used to configure Django when prepare_django() is called.
    """
    from django.apps import apps

    from .exceptions import QDMTKException

    if apps.ready:
        raise QDMTKException(
            "Django was already setup. Ensure `prepare_django` is only called after all datamodels are registered."
        )

    datamodels_registry[datamodel_key] = {
        "apps": installed_apps,
        "db_settings": db_settings,
    }


def prepare_django():
    """
    Sets up Django with all registered apps and database settings
    """
    import django
    from django.apps import apps
    from django.conf import settings

    if apps.ready:
        # already done
        return

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

    # Collect all databases
    databases = {k: v["db_settings"] for k, v in datamodels_registry.items()}
    # Contactenate apps from all datamodels
    installed_apps = []
    for datamodel in datamodels_registry.values():
        installed_apps.extend(datamodel["apps"])

    # Set a default database if needed (required by django)
    if "default" not in databases:
        databases["default"] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }

    # from qgis.core import QgsMessageLog
    # QgsMessageLog.logMessage(f"Setting up Django with {databases=} {installed_apps=}", "QDMTK")

    settings.configure(
        DATABASES=databases,
        INSTALLED_APPS=installed_apps,
        DATABASE_ROUTERS=["qdmtk.router.QDMTKDatabaseRouter"],
        **additionnal_settings,
    )
    django.setup()
