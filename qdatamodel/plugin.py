import os.path

from qgis.core import (
    Qgis,
    QgsProject,
    QgsProviderMetadata,
    QgsProviderRegistry,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .provider import Provider


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
        self.datamodel_action = QAction(
            QIcon(os.path.join(self.plugin_dir, "icon.svg")), "Datamodel", self.toolbar
        )
        self.datamodel_action.triggered.connect(self.init_datamodel)
        self.toolbar.addAction(self.datamodel_action)

    def unload(self):
        self.iface.mainWindow().removeToolBar(self.toolbar)
        # seems this does not exist ? can we still autoreload
        # QgsProviderRegistry.instance().unregisterProvider(Provider.providerKey())

    def init_datamodel(self, checked):

        structure = QgsVectorLayer("Structure", "Structures", Provider.providerKey())
        QgsProject.instance().addMapLayer(structure)

        building = QgsVectorLayer("Building", "Buildings", Provider.providerKey())
        QgsProject.instance().addMapLayer(building)

        monument = QgsVectorLayer("Monument", "Monuments", Provider.providerKey())
        QgsProject.instance().addMapLayer(monument)

        self.iface.messageBar().pushMessage(
            "Success", "Running Datamodel", level=Qgis.Info
        )
