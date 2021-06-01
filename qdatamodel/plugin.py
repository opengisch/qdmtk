import os.path
from io import StringIO

import django
from django.core.management import call_command
from qgis.core import (
    Qgis,
    QgsProject,
    QgsProviderMetadata,
    QgsProviderRegistry,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from .provider import Provider


class Plugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Init Django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qdatamodel.model.settings")
        django.setup()

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Register our provider
        metadata = QgsProviderMetadata(
            Provider.providerKey(), Provider.description(), Provider.createProvider
        )
        QgsProviderRegistry.instance().registerProvider(metadata)

        # Add toolbar
        self.toolbar = self.iface.addToolBar("Datamodel")

        self.datamodel_action = QAction(
            QIcon(os.path.join(self.plugin_dir, "icon.svg")), "Datamodel", self.toolbar
        )
        self.datamodel_action.triggered.connect(self.init_datamodel)
        self.toolbar.addAction(self.datamodel_action)

        self.migrate_action = QAction("Migrate", self.toolbar)
        self.migrate_action.triggered.connect(self.migrate)
        self.toolbar.addAction(self.migrate_action)

        self.showmigrations_action = QAction("Show migrations", self.toolbar)
        self.showmigrations_action.triggered.connect(self.showmigrations)
        self.toolbar.addAction(self.showmigrations_action)

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

    def init_datamodel(self, checked):

        for model in django.apps.apps.get_models():
            layer = QgsVectorLayer(
                model.__name__, model.__name__, Provider.providerKey()
            )
            QgsProject.instance().addMapLayer(layer)

        self.iface.messageBar().pushMessage(
            "Success", "Running Datamodel", level=Qgis.Info
        )
