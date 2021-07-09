from django.apps import apps

from . import datamodels_registry


class QDMTKDatabaseRouter:
    """
    This routes each model to the database corresponding to the datamodel that installed this model
    """

    registry = {}

    def db_for_read(self, model, **hints):
        app = apps.get_app_config(model._meta.app_label)
        for datamodel_key in datamodels_registry:
            if app.name in datamodels_registry[datamodel_key]["apps"]:
                return datamodel_key
        raise Exception(f"No datamodel found {model} (of app {model._meta.app_label})")

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # NOTE : This isn't well used by Django. Even when migrations are not allowed against a database,
        # the corresponding migrations re inserted in the django_migrations tables and listed in
        # django showmigrations.
        # See https://code.djangoproject.com/ticket/23273

        # When migrate is run on a DB that doens't belong to the datamodels (for instance
        # if migrate was called without --database in which case db='default'), we skip the model
        if db not in datamodels_registry:
            return False

        # Otherwise, we only run if the model's app is listed as an installed app of the given
        # datamodel.
        app = apps.get_app_config(app_label)
        return app.name in datamodels_registry[db]["apps"]
