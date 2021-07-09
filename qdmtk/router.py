from django.apps import apps

from . import datamodels_registry

# from qgis.core import (
#     Qgis,
#     QgsCoordinateReferenceSystem,
#     QgsDataSourceUri,
#     QgsProject,
#     QgsProviderMetadata,
#     QgsProviderRegistry,
#     QgsVectorLayer, QgsMessageLog
# )


class QDMTKDatabaseRouter:

    registry = {}

    def db_for_read(self, model, **hints):
        print(f"Routing {model}...", "QDMTK")
        app = apps.get_app_config(model._meta.app_label)
        for datamodel_key in datamodels_registry:
            if app.name in datamodels_registry[datamodel_key]["apps"]:
                print(f"Routing {model} to {datamodel_key}", "QDMTK")
                return datamodel_key
        raise Exception(f"No datamodel found {model} (of app {model._meta.app_label})")

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    # def allow_migrate(self, db, app_label, model_name=None, **hints):
    #     if db not in datamodels_registry:
    #         print(f"(unknown db {app_label}/{model_name} in {db})", "QDMTK")
    #         return False
    #     app = apps.get_app_config(app_label)
    #     allowed = app.name in datamodels_registry[db]["apps"]
    #     if allowed:
    #         print(f"ALLOWING MIGRATION FOR {app_label}/{model_name} IN {db}", "QDMTK")
    #     else:
    #         print(f"(not allowed {app_label}/{model_name} in {db})", "QDMTK")
    #     return allowed
