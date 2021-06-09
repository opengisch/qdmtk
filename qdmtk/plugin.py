import os.path
from io import StringIO

import django
from django.conf import settings
from django.core.management import call_command
from qgis.core import (
    Qgis,
    QgsDataSourceUri,
    QgsProject,
    QgsProviderMetadata,
    QgsProviderRegistry,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from .provider import Provider
from .utils import find_geom_field, find_pk_field


class Plugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Register our provider
        metadata = QgsProviderMetadata(
            Provider.providerKey(), Provider.description(), Provider.createProvider
        )
        QgsProviderRegistry.instance().registerProvider(metadata)

        # Add toolbar
        self.toolbar = self.iface.addToolBar("Datamodel")

        self.load_layers_dj_action = QAction(
            QIcon(os.path.join(self.plugin_dir, "icon_dj.svg")),
            "Load datamodel layers (using Django provider)",
            self.toolbar,
        )
        self.load_layers_dj_action.triggered.connect(self.load_layers_dj)
        self.toolbar.addAction(self.load_layers_dj_action)

        self.load_layers_pg_action = QAction(
            QIcon(os.path.join(self.plugin_dir, "icon_pg.svg")),
            "Load datamodel layers (using Postgres provider)",
            self.toolbar,
        )
        self.load_layers_pg_action.triggered.connect(self.load_layers_pg)
        self.toolbar.addAction(self.load_layers_pg_action)

        self.migrate_action = QAction("Migrate", self.toolbar)
        self.migrate_action.triggered.connect(self.migrate)
        self.toolbar.addAction(self.migrate_action)

        self.showmigrations_action = QAction("Show migrations", self.toolbar)
        self.showmigrations_action.triggered.connect(self.showmigrations)
        self.toolbar.addAction(self.showmigrations_action)

        # Uncomment this to load the demo datamodel
        # from . import register_datamodel
        # from .qdmtkdemo import config
        # register_datamodel(config.DATAMODEL_NAME, config.INSTALLED_APPS, config.DATABASE)

    def unload(self):
        self.iface.mainWindow().removeToolBar(self.toolbar)
        # seems this does not exist ? can we still autoreload
        # QgsProviderRegistry.instance().unregisterProvider(Provider.providerKey())

    def migrate(self):
        out = StringIO()
        call_command("migrate", stdout=out)
        QMessageBox.information(
            self.iface.mainWindow(), "Migration results", out.getvalue()
        )

    def showmigrations(self):
        out = StringIO()
        call_command("showmigrations", stdout=out)
        QMessageBox.information(
            self.iface.mainWindow(), "Current migrations state", out.getvalue()
        )

    def load_layers_dj(self, checked):
        for model in django.apps.apps.get_models():
            if not getattr(model, "qdmtk_addlayer", False):
                continue
            layer = QgsVectorLayer(
                model.__name__, model.__name__, Provider.providerKey()
            )
            QgsProject.instance().addMapLayer(layer)

        self.iface.messageBar().pushMessage(
            "Success", "Loaded Datamodel", level=Qgis.Info
        )

    def load_layers_pg(self, checked):
        for model in django.apps.apps.get_models():
            if not getattr(model, "qdmtk_addlayer", False):
                continue
            db = settings.DATABASES["default"]
            uri = QgsDataSourceUri()
            uri.setConnection(
                db["HOST"], db["PORT"], db["NAME"], db["USER"], db["PASSWORD"]
            )
            query = f"({model.objects.all().query})"
            geom_field = getattr(find_geom_field(model), "name", None)
            key_field = getattr(find_pk_field(model), "name", None)
            uri.setDataSource(
                None,
                query,
                geom_field,
                aKeyColumn=key_field,
            )
            layer = QgsVectorLayer(uri.uri(), model.__name__, "postgres")
            QgsProject.instance().addMapLayer(layer)

        self.iface.messageBar().pushMessage(
            "Success", "Loaded Datamodel", level=Qgis.Info
        )
