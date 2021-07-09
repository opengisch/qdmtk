# Generated by Django 3.2.3 on 2021-06-01 16:46

from django.contrib.gis.db import models
from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Structure",
            fields=[
                ("id", models.BigAutoField(primary_key=True)),
                ("name", models.CharField(max_length=255)),
                ("label", models.CharField(max_length=255)),
                ("geom", models.PointField(srid=4326)),
            ],
        ),
    ]
