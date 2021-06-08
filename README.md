# QDMTK - QGIS datamodel tookit

QDMTK is a framework to build, maintain and use advanced datamodels in QGIS.

The datamodel itself is defined using Django models loaded directly in QGIS with a dedicated python provider.

This has many advantages over a more naive approach using plain SQL init scripts
- Clean datamodel definition, structured in the well known Django way.
- Integrates with Django migrations infrastructure, both for initializing and upgrading the datamodel, allowing multiple instances of the same datamodel to be upgraded independently.
- Same definitions can be used for all databases supported by GeoDjango (Postgis, Spatialite, Mysql, Oracle)
- Full support for type of inheritance supported by Django (concrete table, joined table)
- Ability to use the Django ORM for advanced business logic (custom plugin actions, web interface, etc.), including third party packages such as `django-compoutedfields`, `django-pgtrigger` or `django-migrate-sql-deux`.
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

## Limitations

- No integration with the Django user/permissions framework (the ORM connects directly to the database, hence only native Postgres permissions can be used)
- Probably quite slow. For better performance, we may try proxying native Postgres/Sqlite provider for reading (using the ORM to build the select statement with inheritance), and Django instances only for update queries


## Usage

```bash
# 1. Initialize the datamodel
python manage.py migrate
```


## Dev cycle

```bash
# 1. Make some changes to the datamodel
vim qdmtk/model/core/datamodel.py

# 2. Autogenerate a migration
python manage.py makemigrations

# 3. Review and adapt the migration
vim qdmtk/model/core/migrations/0001_initial.py

# 4. Apply the migration
python manage.py migrate
```

## Notes

### Django

- Schemas not supported out of the box. We could probably add a hack that moves all tables to custom schemas after migration, and add Postgres search paths according to loaded apps (see https://stackoverflow.com/a/28452103/13690651).
