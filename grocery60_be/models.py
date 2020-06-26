from django.db import models


class Store(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )
    address = models.CharField(
        max_length=50
    )
    city = models.CharField(
        max_length=50
    )
    state = models.CharField(
        max_length=50
    )
    zip = models.CharField(
        max_length=50
    )
    country = models.CharField(
        max_length=50
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "store"