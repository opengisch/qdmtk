from django.contrib.gis.db import models


class Structure(models.Model):
    qdmtk_addlayer = True

    id = models.BigAutoField(primary_key=True)
    geom = models.PointField(srid=4326)
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.label = f"[{self.id}] {self.name}"
        super().save(*args, **kwargs)


class Building(Structure):
    qdmtk_addlayer = True

    stories_count = models.IntegerField()
