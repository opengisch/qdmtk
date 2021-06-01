# QDMTK - QGIS datamodel tookit

QDMTK is a framework to build, maintain and use advanced datamodels in QGIS.

The datamodel itself is defined using SQLAlchemy loaded directly in QGIS with a dedicated python provider.

This has many advantages over a more naive approach using plain SQL init scripts
- Clean datamodel definition.
- *TODO* Preconfigured pdoc setup to auto-generate documentation of the datamodel.
- Same definitions can be used for Postgis and Sqlite.
- Full support for any type of inheritance supported by SQLAlchemy (single table, concrete table, joined table)
- *TODO* Integrates with Alembic, a mature SQLAlchemy migration tool, both for initializing and upgrading the datamodel, allowing multiple instances of the same datamodel to be upgraded independently.
- *TODO* Ability to use the SQLAlchemy ORM for advanced business logic (custom plugin actions, web interface, etc.)

## Usage

```bash
# 1. Initialize the datamodel
alembic upgrade head

```

## Dev cycle

```bash
# 1. Make some changes to the datamodel
vim qdatamodel/model/core.py

# 2. Autogenerate a migration
alembic revision --autogenerate -m "changes"

# 3. Review and adapt the migration
vim qdatamodel/model/alembic/versions/20210101_initial_1234567890ab

# 4. Apply the migration
alembic upgrade head
```


## Notes

### SQLAlchemy + Alembic

- Migrations : not as nice as Django. Migrations have no state management, meaning the ORM can't be used in database migrations.
- Geoalchemy2 + Alembic : not well supported, indexes and support table not recognized by Alembic (Alembic wants to drop spatial indices and support tables on each autogenerated migrations)
- Not easy to make modular applications (but not impossible, see https://medium.com/@karuhanga/of-modular-alembic-migrations-e94aee9113cd)
