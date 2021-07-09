from django.contrib.gis.db import models


class LandLot(models.Model):
    qdmtk_addlayer = True

    id = models.BigAutoField(primary_key=True)
    geom = models.PolygonField(srid=4326)
    owner = models.ForeignKey("app_b.owner", null=True, on_delete=models.SET_NULL)
