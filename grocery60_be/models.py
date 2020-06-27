from django.db import models
from django.contrib.auth.models import User, Group


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
    nearby_zip = models.CharField(
        max_length=50
    )
    country = models.CharField(
        max_length=50
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "store"


class Product(models.Model):
    product_name = models.CharField(
        max_length=50,
        unique=True,
    )
    product_url = models.CharField(
        max_length=200
    )
    product_category = models.CharField(
        max_length=200
    )
    price = models.CharField(
        max_length=50
    )
    media = models.CharField(
        max_length=100
    )
    caption = models.CharField(
        max_length=100
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "product"

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    last_access = models.CharField(
        max_length=50
    )
    extra = models.CharField(
        max_length=200
    )
    salutation = models.CharField(
        max_length=5
    )
    phone_number = models.CharField(
        max_length=128
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "customer"


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    extra = models.CharField(
        max_length=200,
        blank=True
    )
    billing_address_id = models.IntegerField(blank=True)
    customer_id = models.IntegerField()
    shipping_address_id = models.IntegerField(blank=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "cart"

