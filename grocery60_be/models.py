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
    media = models.CharField(
        max_length=500
    )
    image = models.FileField(
        blank=True
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
    price = models.DecimalField(max_digits=6, decimal_places=2)
    media = models.CharField(
        max_length=500
    )
    caption = models.CharField(
        max_length=100
    )
    extra = models.CharField(
        max_length=200,
        blank=True
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    image = models.FileField(
        blank=True
    )


    def __str__(self):
        return self.name

    class Meta:
        db_table = "product"

class Customer(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    last_access = models.CharField(
        max_length=50,
        blank=True
    )
    extra = models.CharField(
        max_length=200,
        blank=True
    )
    salutation = models.CharField(
        max_length=5,
        blank=True
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

class CartItem(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    extra = models.CharField(
        max_length=200,
        blank=True
    )
    quantity = models.IntegerField()
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    class Meta:
        db_table = "cartitem"

class BillingAddress(models.Model):
    priority = models.IntegerField()
    name = models.CharField(
        max_length=1024
    )
    company_name = models.CharField(
        max_length=1024,
        blank=True
    )
    address = models.CharField(
        max_length=1024
    )
    house_number =  models.CharField(
        max_length=12
    )
    zip = models.CharField(
        max_length=12   
    )
    city = models.CharField(
        max_length=1024
    )
    country = models.CharField(
        max_length=3
    )
    customer_id = models.IntegerField()

    class Meta:
        db_table = "billingaddress"


class ShippingAddress(models.Model):    
    priority = models.IntegerField()
    name = models.CharField(
        max_length=1024
    )
    company_name = models.CharField(
        max_length=1024,
        blank=True
    )
    address = models.CharField(
        max_length=1024
    )
    house_number =  models.CharField(
        max_length=12
    )
    zip = models.CharField(
        max_length=12   
    )
    city = models.CharField(
        max_length=1024
    )
    country = models.CharField(
        max_length=3
    )
    customer_id = models.IntegerField()


    class Meta:
        db_table = "shippingaddress"

class Order(models.Model):    
    status = models.CharField(
        max_length=50
    )
    currency = models.CharField(
        max_length=7
    )
    subtotal = models.DecimalField(max_digits=6, decimal_places=2)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    extra = models.CharField(
        max_length=200,
        blank=True
    )
    stored_request = models.CharField(
        max_length=200,
        blank=True
    )
    shipping_address_text = models.CharField(
        max_length=200,
        blank=True
    )
    billing_address_text = models.CharField(
        max_length=200,
        blank=True
    )
    token = models.CharField(
        max_length=40,
        blank=True
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    class Meta:
        db_table = "order"

class OrderItem(models.Model):

    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    line_total = models.DecimalField(max_digits=6, decimal_places=2)
    extra = models.CharField(
        max_length=200
    )
    quantity = models.IntegerField()
    canceled = models.BooleanField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        db_table = "orderitem"

class OrderPayment(models.Model):
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    transaction_id = models.CharField(
        max_length=200
    )
    status = models.CharField(
        max_length=100
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_method = models.CharField(
        max_length=200
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    class Meta:
        db_table = "orderpayment"

class ShippingMethod(models.Model):
    name = models.CharField(
        max_length=255
    )
    carrier = models.CharField(
        max_length=32
    )
    min_weight = models.DecimalField(max_digits=6, decimal_places=2)
    max_weight = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shippingmethod"


class Delivery(models.Model):
    fulfilled_at = models.DateTimeField(blank=True)
    shipped_at = models.DateTimeField(blank=True)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    class Meta:
        db_table = "delivery"




