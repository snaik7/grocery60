import decimal
from datetime import datetime
from decimal import Decimal
import requests
import json

from django.db import models, connection
from django.contrib.auth.models import AbstractUser

from grocery60_be import email as email_send
from grocery60_be import settings
from grocery60_be.error import ValidationError


class User(AbstractUser):
    verified = models.CharField(
        max_length=1,
        default='Y'
    )
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "auth_user"


class Store(models.Model):
    store_id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=50
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
        max_length=500
    )
    country = models.CharField(
        max_length=50
    )
    store_url = models.CharField(
        max_length=500,
        blank=True
    )
    image = models.FileField(
        blank=True
    )
    email = models.CharField(
        max_length=50
    )
    phone = models.CharField(
        max_length=50
    )
    status = models.CharField(
        max_length=20
    )
    currency = models.CharField(
        max_length=3,
        default='usd',
        blank=True
    )
    payment_account = models.CharField(
        max_length=50,
        blank=True
    )

    def save(self, *args, **kwargs):
        self.currency = self.currency.lower()
        self.status = self.status.upper()
        return super(Store, self).save(*args, **kwargs)

    class Meta:
        db_table = "store"


class StoreAdmin(models.Model):
    username = models.CharField(
        max_length=50,
        unique=True,
    )
    password = models.CharField(
        max_length=128,
        blank=True
    )
    phone_number = models.CharField(
        max_length=128
    )
    email = models.CharField(
        max_length=100
    )
    secret = models.CharField(
        max_length=150,
        blank=True
    )
    status = models.CharField(
        max_length=10
    )
    is_superuser = models.BooleanField(blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    class Meta:
        db_table = "storeadmin"


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(
        max_length=500
    )
    product_url = models.CharField(
        max_length=200,
        blank=True
    )
    product_category = models.CharField(
        max_length=200
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    media = models.CharField(
        max_length=500,
        blank=True
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
    status = models.CharField(
        max_length=10
    )
    tax_exempt = models.BooleanField(blank=True, default=False)

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
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

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
    house_number = models.CharField(
        max_length=12
    )
    zip = models.CharField(
        max_length=12
    )
    city = models.CharField(
        max_length=1024
    )
    state = models.CharField(
        max_length=2
    )
    country = models.CharField(
        max_length=100
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
    house_number = models.CharField(
        max_length=12
    )
    zip = models.CharField(
        max_length=12
    )
    city = models.CharField(
        max_length=1024
    )
    state = models.CharField(
        max_length=2
    )
    country = models.CharField(
        max_length=100
    )
    customer_id = models.IntegerField()

    class Meta:
        db_table = "shippingaddress"


class Count(models.Model):
    count = models.IntegerField()


def get_tax(state):
    tax = Tax.objects.get(state=state)
    return Decimal(tax.tax)


def get_discount(customer_id, sub_total):
    discount = Decimal(settings.DISCOUNT) / Decimal(100) * Decimal(sub_total)
    cents = Decimal('.01')
    discount = discount.quantize(cents, decimal.ROUND_HALF_UP)
    return discount


def get_shipping_cost(shipping_id, customer_id):
    print('get_shipping_cost')
    shipping_cost = Decimal('0')
    shipping_extra = Decimal('0')
    if shipping_id:
        shipping_method = ShippingMethod.objects.get(id=shipping_id)
        if shipping_method.name == 'Store Pickup':
            shipping_cost = Decimal(shipping_method.price) + 1
        else:
            print('not store pickup')
            shipping_address = ShippingAddress.objects.get(customer_id=customer_id)
            destination = shipping_address.address + ' ' + shipping_address.house_number + ', ' + \
                          shipping_address.city + ', ' + shipping_address.country + ', ' + shipping_address.zip

            store = Store.objects.get(store_id=shipping_method.store_id)
            origin = store.address + ', ' + store.city + ', ' + \
                     store.country + ', ' + store.zip

            resp = requests.get('https://maps.googleapis.com/maps/api/distancematrix/xml?origins=' + origin +
                                '&destinations=' + destination + '&mode=car&units=imperial&key=' + settings.API_KEY)

            print(resp.status_code)
            if resp.status_code != 200:
                print('dist response ' + resp.text)
                raise ValidationError('Google distance API failed to retrieve distance to calculate shipping')
            else:
                print('dist response ' + resp.text)
            distance_resp = json.loads(resp.text)
            distance = distance_resp.get('rows')[0].get('elements')[0].get('distance')
            distance = distance.replace(' mi', '')
            print('distance', distance)

            if distance > 10:
                shipping_extra = (distance - 10) * settings.DELIVERY_PER_MILE

        shipping_cost = Decimal(shipping_cost) + Decimal(shipping_extra)
        cents = Decimal('.01')
        shipping_cost = shipping_cost.quantize(cents, decimal.ROUND_HALF_UP)

    return shipping_cost


def get_tip(tip, custom_tip, sub_total, no_tax_total):
    tip_amount = Decimal('0.00')
    if custom_tip:
        tip_amount = Decimal(custom_tip)
    elif tip:
        tip_amount = (Decimal(sub_total) + Decimal(no_tax_total)) * Decimal(tip) / Decimal(100)

    cents = Decimal('.01')
    tip_amount = tip_amount.quantize(cents, decimal.ROUND_HALF_UP)
    return tip_amount


def get_service_fee(sub_total, country):
    service_fee = Decimal(settings.SERVICE_FEE) / Decimal(100) * Decimal(sub_total)
    if country == 'IN':
        service_fee = Decimal(50) if service_fee < 50 else service_fee
    else:
        service_fee = Decimal(7) if service_fee < 7 else service_fee
    cents = Decimal('.01')
    service_fee = service_fee.quantize(cents, decimal.ROUND_HALF_UP)
    return service_fee


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    currency = models.CharField(
        max_length=7
    )
    subtotal = models.DecimalField(max_digits=6, decimal_places=2)
    tip = models.DecimalField(max_digits=6, decimal_places=2)
    service_fee = models.DecimalField(max_digits=6, decimal_places=2)
    tax = models.DecimalField(max_digits=6, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, default='0')
    discount = models.DecimalField(max_digits=6, decimal_places=2)
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
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10
    )

    class Meta:
        db_table = "shippingmethod"


class OrderPayment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    transaction_id = models.CharField(
        max_length=200,
        unique=True
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
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    payout_status = models.CharField(
        max_length=50,
        blank=True
    )
    payout_message = models.CharField(
        max_length=100,
        blank=True
    )
    payout_id = models.CharField(
        max_length=50,
        blank=True
    )
    correlation_id = models.CharField(
        max_length=50,
        blank=True
    )
    signature = models.CharField(
        max_length=150,
        blank=True
    )
    shippingmethod = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)

    def record_payment(self, data, intent):
        try:
            amount = data.get('amount')
            transaction_id = intent.get('id')
            if data.get('card'):
                payment_method = 'Card ending in ' + data.get('card').get('number')[12:16]
            else:
                payment_method = 'Razor Pay'
            order_id = data.get('metadata').get('order_id')
            store_id = data.get('metadata').get('store_id')
            shippingmethod_id = data.get('metadata').get('shippingmethod_id')
            status = "CONFIRMED"
            correlation_id = intent.get('id')
            signature = None
            order_payment = OrderPayment(amount=amount, transaction_id=transaction_id, payment_method=payment_method,
                                         order_id=order_id, status=status, store_id=store_id,
                                         correlation_id=correlation_id,
                                         signature=signature, shippingmethod_id=shippingmethod_id)
            order_payment.save()
        except Exception as e:
            raise ValidationError('Order Payment failed for Order = ' + str(order_id) + ' Order Payment failed for '
                                                                                        'Order = ' + str(
                order_id) + ' with ' + str(e))
        return order_payment.payment_id

    def delete_cart(self, data):
        try:
            cart = None
            customer_id = data.get('customer_id')
            if not customer_id:
                customer_id = data.get('metadata').get('customer_id')
            cart = Cart.objects.get(customer_id=customer_id)
            if cart:
                cart.delete()
        except Exception as e:
            print('Exception in deleting cart ' + str(e))

    def send_pickup_email(self, email):
        print('data received ', email.order_id)
        print('data received ', email.order_items_list)
        # email_send.send_email(email, 'order_pickup.html')
        email.template = 'order_pickup.html'
        email_send.send_email_topic(email)

    def send_success_email(self, email):
        print('data received ', email.order_id)
        print('data received ', email.order_items_list)
        email.template = 'order_confirmation.html'
        email_send.send_email_topic(email)

    def send_failure_email(self, transaction_id):
        print('Payment failure data received ' + transaction_id)
        order_payment = OrderPayment.objects.select_related('order').filter(transaction_id=transaction_id).first()
        customer = Customer.objects.get(customer_id=order_payment.order.customer_id)
        email = Email()
        email.subject = "Order failure for Grocery 60"
        email.phone = customer.phone_number
        email.email = customer.email
        email.order_id = order_payment.order_id
        email.template = 'order_payment_failure.html'
        email_send.send_email_topic(email)

    def send_store_email(self, transaction_id):
        print('Store success data received ' + transaction_id)
        order_payment = OrderPayment.objects.select_related('order').filter(correlation_id=transaction_id).first()
        store = Store.objects.get(store_id=order_payment.store.store_id)
        email = Email()
        email.currency = '₹' if store.currency == 'inr' else '$'
        email.subject = "Store Order Confirmation for Grocery 60"
        email.email = store.email
        email.order_id = order_payment.order_id
        email.set_order(email.order_id)
        email.template = 'store_order_confirmation.html'
        email_send.send_email_topic(email)

    def update_payment(self, transaction_id, status):
        try:
            order_payment = OrderPayment.objects.filter(transaction_id=transaction_id).first()
            order_payment.status = status
            if status == "SUCCEEDED":
                order_payment.status = 'READY_TO_FULFILL'
            elif status == "FAILED":
                order_payment.status = 'PAYMENT_FAILURE'
            order_payment.updated_at = datetime.now()
            order_payment.save()
        except Exception as e:
            raise ValidationError(
                'Order Payment failed update in Grocery60 for Order''s  transaction_id = ' + transaction_id + ' with ' + str(
                    e))
        return order_payment.payment_id

    class Meta:
        db_table = "orderpayment"


class Email():
    subject, first_name, username, password, email, order_id, token, template, currency, phone, address, customer_id = None, None, None, None, None, \
                                                                                                                       None, None, None, None, None, None, None
    order_items_list = []
    subtotal, tax, discount, service_fee, tip, shipping_fee, total = 0, 0, 0, 0, 0, 0, 0

    def set_order(self, order_id):
        order = Order.objects.get(order_id=order_id)
        self.token = order.token
        self.subtotal = str(order.subtotal)
        self.tax = str(order.tax)
        self.service_fee = str(order.service_fee)
        self.tip = str(order.tip)
        self.shipping_fee = str(order.shipping_fee)
        self.discount = str(order.discount)
        self.total = str(order.total)
        self.order_items_list = []
        query_set = OrderItem.objects.filter(order_id=order_id).values('product__product_name', 'product__price',
                                                                       'quantity', 'line_total')
        for item in query_set:
            item_list = {}
            print('item', item)
            item_list['product__product_name'] = item.get('product__product_name')
            item_list['product__price'] = str(item.get('product__price'))
            item_list['quantity'] = item.get('quantity')
            item_list['line_total'] = str(item.get('line_total'))
            self.order_items_list.append(item_list)

    def asdict(self):
        return {'token': self.token, 'subtotal': self.subtotal, 'order_items_list': self.order_items_list,
                'tax': self.tax,
                'service_fee': self.service_fee, 'tip': self.tip, 'shipping_fee': self.shipping_fee,
                'discount': self.discount,
                'total': self.total, 'subject': self.subject, 'first_name': self.first_name, 'username': self.username,
                'password': self.password, 'email': self.email, 'order_id': self.order_id, 'template': self.template,
                'currency': self.currency, 'phone': self.phone, 'address': self.address}


class Tax(models.Model):
    state = models.CharField(
        max_length=2,
        unique=True
    )
    country = models.CharField(
        max_length=100,
        unique=True
    )
    country_code = models.CharField(
        max_length=2,
        unique=True
    )
    tax = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        db_table = "tax"


class Category(models.Model):
    category = models.CharField(
        max_length=50
    )

    class Meta:
        db_table = "category"


class Leads(models.Model):
    customer_id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    request = models.CharField(
        max_length=500
    )
    email = models.CharField(
        max_length=128
    )
    phone_number = models.CharField(
        max_length=128
    )
    status = models.CharField(
        max_length=50,
        default='ACTIVE'
    )
    comments = models.CharField(
        max_length=100,
        blank=True
    )

    class Meta:
        db_table = "leads"
