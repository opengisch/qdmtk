from django.contrib.gis.db import models


def string_to_fid(string):
    """
    Converts a string to a longlong, matching QGIS's STRING_TO_FID macro
    """
    try:
        return int(string)
    except ValueError:
        return 0


def find_geom_field(model):
    for field in model._meta.get_fields():
        if isinstance(field, models.GeometryField):
            return field
    return None


def find_pk_field(model):
    return model._meta.pk
