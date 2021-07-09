from django.contrib.gis.db import models


class Owner(models.Model):
    qdmtk_addlayer = True

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
