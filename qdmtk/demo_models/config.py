import os
import tempfile

PROJECTNAME_A = "demo_project_a"
DATABASE_A = {
    "ENGINE": "django.contrib.gis.db.backends.spatialite",
    "NAME": os.path.join(tempfile.gettempdir(), f"qdmtk_demo_project_a.db"),
}
APPS_A = ["qdmtk.demo_models.app_a"]


PROJECTNAME_B = "demo_project_b"
DATABASE_B = {
    "ENGINE": "django.contrib.gis.db.backends.spatialite",
    "NAME": os.path.join(tempfile.gettempdir(), f"qdmtk_demo_project_b.db"),
}
APPS_B = ["qdmtk.demo_models.app_b", "qdmtk.demo_models.app_c"]
