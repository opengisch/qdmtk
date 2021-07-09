import sys

from django.core.management import execute_from_command_line

from qdmtk import prepare_django, register_datamodel
from qdmtk.demo_models import config

if __name__ == "__main__":
    register_datamodel(config.PROJECTNAME_A, config.APPS_A, config.DATABASE_A)
    register_datamodel(config.PROJECTNAME_B, config.APPS_B, config.DATABASE_B)
    prepare_django()
    execute_from_command_line(sys.argv)
