import asyncio
import decimal
from datetime import datetime
from decimal import Decimal

from django.db import models, connection
from django.contrib.auth.models import User
from grocery60_be import email as email_send
from grocery60_be import settings


class Store(models.Model):
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
        max_length=50
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
    payment_account = models.CharField(
        max_length=50,
        blank=True
    )

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
        max_length=150
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
    product_name = models.CharField(
        max_length=50
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

    def search_catalog(self, search_key, store_id):
        if search_key and store_id:
            search_list = search_key.split()
            if len(search_list) > 2:
                response_dict = {
                    # the format of error message determined by you base exception class
                    'msg': 'Refine search criteria'
                }
                status = 403
                return response_dict, status
            elif len(search_list) > 0:
                search_query = self.get_search_query(search_list, store_id)
            else:
                response_dict = {
                    # the format of error message determined by you base exception class
                    'msg': 'No search criteria found'
                }
                status = 403
                return response_dict, status
        else:
            response_dict = {
                # the format of error message determined by you base exception class
                'msg': 'No search criteria found'
            }
            status = 200
            return response_dict, status
        print('Search query ', search_query[0], ' criteria ', search_query[1])
        with connection.cursor() as cursor:
            cursor.execute(search_query[0], search_query[1])
            row = self.dictfetchall(cursor)
        status = 200
        return row, status

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def get_search_query(self, search_list, store_id):
        if len(search_list) == 1:
            query_search_list = search_list * 2
            query = "SELECT id, product_name, product_url, product_category, media, caption, store_id, price, extra FROM " \
                    "product WHERE  (lower(product_name) ~ %s OR lower(extra) ~ %s) AND store_id = %s "
        else:
            query_search_list = search_list * 2
            query = "SELECT id, product_name, product_url, product_category, media, caption, store_id, price, extra FROM " \
                    "product WHERE (lower(product_name) ~ %s OR lower(product_name) ~ %s  OR lower(extra) ~ %s OR lower(" \
                    "extra) ~ %s) AND store_id = %s "
        query_search_list.append(store_id)
        return query, query_search_list

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
        max_length=3
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


def get_shipping_cost(shipping_id):
    shipping_cost = Decimal('0')
    if shipping_id:
        shipping_method = ShippingMethod.objects.get(id=shipping_id)
        shipping_cost = Decimal(shipping_method.price)
        cents = Decimal('.01')
        shipping_cost = shipping_cost.quantize(cents, decimal.ROUND_HALF_UP)

    return shipping_cost


def get_tip(tip, custom_tip, sub_total):
    tip_amount = Decimal('0')
    if custom_tip:
        tip_amount = Decimal(custom_tip)
    elif tip:
        tip_amount = Decimal(sub_total) * Decimal(tip) / Decimal(100)

    cents = Decimal('.01')
    tip_amount = tip_amount.quantize(cents, decimal.ROUND_HALF_UP)
    return tip_amount


def get_service_fee(sub_total):
    service_fee = Decimal(settings.SERVICE_FEE) / Decimal(100) * Decimal(sub_total)
    service_fee = Decimal(2) if service_fee < 2 else service_fee
    cents = Decimal('.01')
    service_fee = service_fee.quantize(cents, decimal.ROUND_HALF_UP)
    return service_fee


class Order(models.Model):
    status = models.CharField(
        max_length=50
    )
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


class OrderPayment(models.Model):
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

    def record_payment(self, data, intent):
        try:
            amount = data.get('amount')
            transaction_id = intent.get('id')
            payment_method = 'card'
            order_id = data.get('metadata').get('order_id')
            store_id = data.get('metadata').get('store_id')
            status = intent.get('status')
            correlation_id = intent.get('id')
            signature = None
            order_payment = OrderPayment(amount=amount, transaction_id=transaction_id, payment_method=payment_method,
                                         order_id=order_id, status=status, store_id=store_id,
                                         correlation_id=correlation_id,
                                         signature=signature)
            order_payment.save()
        except Exception as e:
            raise Exception('Order Payment failed for Order = ' + order_id + ' with ' + str(e))
        return order_payment.id

    def delete_cart(self, data):
        try:
            cart = None
            customer_id = data.get('metadata').get('customer_id')
            cart = Cart.objects.get(customer_id=customer_id)
            cart.delete()
        except Exception as e:
            raise Exception('Cart failed to delete = ' + cart.id + ' with ' + str(e))
        return cart.id

    def send_success_email(self, email):
        print('data received ', email.order_id)
        print('data received ', email.order_items_list)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(email_send.send_email(email, 'order_confirmation.html'))

    def send_failure_email(self, transaction_id):
        print('Payment failure data received ' + transaction_id)
        order_payment = OrderPayment.objects.select_related('order').filter(transaction_id=transaction_id).first()
        customer = Customer.objects.get(customer_id=order_payment.order.customer_id)
        email = Email()
        email.subject = "Order failure for Grocery 60"
        email.email = customer.email
        email.order_id = order_payment.order_id
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(email_send.send_email(email, 'order_payment_failure.html'))

    def send_store_email(self, transaction_id):
        print('Store success data received ' + transaction_id)
        order_payment = OrderPayment.objects.select_related('order').filter(transaction_id=transaction_id).first()
        store = Store.objects.get(id=order_payment.store.id)
        email = Email()
        email.subject = "Order Confirmation for Grocery 60"
        email.email = store.email
        email.order_id = order_payment.order_id
        email.set_order(email.order_id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(email_send.send_email(email, 'store_order_confirmation.html'))

    def update_payment(self, transaction_id, status):
        try:
            order_payment = OrderPayment.objects.get(transaction_id=transaction_id)
            order_payment.status = status
            order_payment.updated_at = datetime.now()
            order_payment.save()
            if status == "payment_intent.succeeded":
                order = Order.objects.get(id=order_payment.order_id)
                order.status = 'Ready to fulfill'
                order.save()
            elif status == "payment_intent.payment_failed":
                order = Order.objects.get(id=order_payment.order_id)
                order.status = 'Payment failure'
                order.save()
        except Exception as e:
            raise Exception(
                'Order Payment failed update in Grocery60 for Order''s  transaction_id = ' + transaction_id + ' with ' + str(
                    e))
        return order_payment.id

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


class Email(models.Model):
    subject, first_name, username, password, email, order_id = None, None, None, None, None, None
    order_items_list = []
    subtotal, tax, discount, service_fee, tip, shipping_fee, total = 0, 0, 0, 0, 0, 0, 0

    def set_order(self, order_id):
        order = Order.objects.get(pk=order_id)
        self.subtotal = order.subtotal
        self.tax = order.tax
        self.service_fee = order.service_fee
        self.tip = order.tip
        self.shipping_fee = order.shipping_fee
        self.discount = order.discount
        self.total = order.total

        self.order_items_list = list(
            OrderItem.objects.filter(order_id=order_id).values('product__product_name', 'product__price',
                                                               'quantity', 'line_total'))


class Tax(models.Model):
    state = models.CharField(
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
