"""initial c data

Revision ID: 35fd4d0ef997
Revises: b65334d397fa
Create Date: 2021-05-31 20:22:28.937934

"""
from alembic import op
from sqlalchemy.orm.session import Session

# revision identifiers, used by Alembic.
revision = "35fd4d0ef997"
down_revision = "b65334d397fa"
branch_labels = None
depends_on = None


def upgrade():
    # Session = sessionmaker(bind=engine)

    # Initial data
    session = Session(bind=op.get_bind())

    # Aouch... we can't use the ORM for data migrations as there's no state
    # like in Django... see https://stackoverflow.com/a/36087108/13690651

    # if session.query(Building).count() == 0:
    #     session.add(
    #         Building(
    #             name="my house",
    #             stories_count=4,
    #             # geom="SRID=4326;POINT(6.14 46.20)",
    #         )
    #     )
    #     session.add(
    #         Structure(
    #             name="your house",
    #             # geom="SRID=4326;POINT(6.16 46.21)",
    #         )
    #     )
    #     session.commit()
    # session.close()


def downgrade():
    pass
