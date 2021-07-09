# QDMTK - QGIS datamodel tookit

**WARNING - THIS IS IN EARLY DEVELOPEMENT, NOT STABLE/USABLE YET**

QDMTK is a framework to build, maintain and use advanced datamodels in QGIS using the Django ORM.

It offers a QGIS plugin with the following features:
- an infrastructure allowing to integrate Django datamodels in QGIS plugins
- a GUI to show and run migrations
- a provider to load Django models as QGIS layers (with all Django ORM benefits, inheritance, signals, custom save logic, etc)
- an alternative native way to load the Django models using a regular Postgres layer (readonly) using the ORM's generated query


Using the Django ORM has many advantages over a more naive approach using plain SQL init scripts:

- Clean datamodel definition, structured in the well known Django way.
- Integrates with Django migrations infrastructure, both for initializing and upgrading the datamodel, allowing multiple instances of the same datamodel to be upgraded independently.
- Same definitions can be used for all databases supported by GeoDjango (Postgis, Spatialite, Mysql, Oracle)
- Full support for type of inheritance supported by Django (concrete table, joined table)
- Ability to use the Django ORM for advanced business logic (custom plugin actions, web interface, etc.), including third party packages such as `django-computedfields`, `django-pgtrigger` or `django-migrate-sql-deux`.
- Ability to user other Django facilities such as management commands, shell, fixtures, error reporting, etc.
- *TODO* Preconfigured pdoc setup to auto-generate documentation of the datamodel.


## Roadmap

- [ ] Implement transaction (incl. transaction pool)
- [ ] Test performance
- [ ] Customizable settings
  - [ ] Database connection string (connecting by service name incoming in Django 4.0, [see here](https://docs.djangoproject.com/en/dev/releases/4.0/#django-contrib-postgres))
  - [ ] List of installed apps
- [ ] Improve migration feedback when missing migrations (see https://github.com/django/django/pull/14246)
- [ ] Autoconfigure QGIS layers (relation widgets, default label, readony fields, etc)
- [ ] Think about how QDMTK and datamodels can be distributed (can we separate distribution, can we use multiple independent models/databases, etc)
- [ ] As contrib apps for Postgres:
  - [ ] Django Users -> Postgres user syncing to allow enforcing permissions at QGIS level
  - [ ] Automatically organize tables in schemas according to apps

## Limitations

- No integration with the Django user/permissions framework yet (the ORM connects directly to the database, hence only native Postgres permissions can be used)
- Probably quite slow. For better performance, we may try proxying native Postgres/Sqlite provider for reading (using the ORM to build the select statement with inheritance), and Django instances only for update queries

## Conventions

Datamodels are regular Django ORM models. Refer to the [Django ORM documentation](https://docs.djangoproject.com/en/3.2/topics/db/models/) for more information.

Additionnaly to Django's definition, the custom conventions can be used :

```
class MyModel(models.Model):
    # Whether a QGIS layer should be created by the plugin's load_layers action
    qdmtk_addlayer = True
```

## Integrations in a QGIS plugin

To register a datamodels from a QGIS plugin, add the following code to the `__init__` and `initGui` methods:

```python
# ...
from qdmtk import register_datamodel, prepare_django

class Plugin:

    def __init__(self, iface):
        # ...
        datamodel_key = "demo"  # unique name of your datamodel
        installed_apps = ["qdmtk.demo_models.app_a", "qdmtk.demo_models.app_b"]  # list of django apps, see django settings docs
        database_settings = {  # database connection settings, see django settings docs
            "ENGINE": "django.contrib.gis.db.backends.spatialite",
            "NAME": os.path.join(tempfile.gettempdir(), f"mydatabase.db"),
        }
        register_datamodel(datamodel_key, installed_apps, database_settings)

        # This is only required if you don't want to depend on the QDMTK plugin
        iface.initializationCompleted.connect(prepare_django)

    # ...
```

## Dev cycle

```bash

# 0. If you want to use this without depending on the QDMTK plugin being installed (and/or outside of QGIS), we need to install qdmtk
pip install qdmtk

# 1. Make some changes to the datamodel
vim qdmtk/qdmtkdemo/datamodel.py

# 2. Autogenerate a migration
python manage.py makemigrations

# 3. Review and adapt the migration
vim qdmtk/qdmtkdemo/migrations/0001_initial.py

# 4. Apply the migration
python manage.py migrate
```

## Deployment

QDMTK is deployed automatically on git tags `v*` to both the QGIS plugin repository and PyPi.

## Notes

###

### GDAL/GEOS paths

When used within QGIS, Spatial libraries should be found, but when running this as standalone, you may need to manually specify paths to GDAL and GEOS libraries. This can be done with the following env variables.
```
# Windows Powershell
$Env:GDAL_LIBRARY_PATH = "C:\OSGeo4W\bin\gdal302.dll"
$Env:GEOS_LIBRARY_PATH = "C:\OSGeo4W\bin\geos_c.dll"
$Env:SPATIALITE_LIBRARY_PATH = "C:\OSGeo4W\bin\mod_spatialite.dll"
```

### Schemas

Schemas are not supported out of the box. We could probably add a hack that moves all tables to custom schemas after migration, and add Postgres search paths according to loaded apps (see https://stackoverflow.com/a/28452103/13690651).
