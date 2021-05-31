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
