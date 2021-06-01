# QDMTK - QGIS datamodel tookit

QDMTK is a framework to build, maintain and use advanced datamodels in QGIS.

The datamodel itself is defined using Django models loaded directly in QGIS with a dedicated python provider.

This has many advantages over a more naive approach using plain SQL init scripts
- Clean datamodel definition.
- *TODO* Preconfigured pdoc setup to auto-generate documentation of the datamodel.
- Same definitions can be used for Postgis and Sqlite.
- Full support for type of inheritance supported by Django concrete table, joined table)
- *TODO* Integrates with Django migrations infrastructure, both for initializing and upgrading the datamodel, allowing multiple instances of the same datamodel to be upgraded independently.
- *TODO* Ability to use the Django ORM for advanced business logic (custom plugin actions, web interface, etc.)

## Usage

```bash
# 1. Initialize the datamodel
python manage.py migrate

```

## Dev cycle

```bash
# 1. Make some changes to the datamodel
vim qdatamodel/model/core/datamodel.py

# 2. Autogenerate a migration
python manage.py makemigrations

# 3. Review and adapt the migration
vim qdatamodel/model/core/migrations/0001_initial.py

# 4. Apply the migration
python manage.py migrate
```


## Notes

### Django

- Schemas not supported out of the box. We could probably add a hack that moves all tables to custom schemas after migration, and add Postgres search paths according to loaded apps (see https://stackoverflow.com/a/28452103/13690651).
