import base64
import decimal
from decimal import Decimal

from django.contrib.auth import hashers
#from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import JSONParser
from django.http import JsonResponse
from grocery60_be import email as email_send, search_product, settings, serializers
from grocery60_be import util

from google.cloud import storage

from grocery60_be.error import ValidationError
from grocery60_be.models import Cart, CartItem, Customer, Product, Store, BillingAddress, ShippingAddress, Order, \
    OrderItem, OrderPayment, ShippingMethod, Delivery, Tax, Email, StoreAdmin, Category, User
from grocery60_be.serializers import CartSerializer, CartItemSerializer, CustomerSerializer, CatalogSerializer, \
    StoreSerializer, BillingAddressSerializer, ShippingAddressSerializer, OrderSerializer, OrderItemSerializer, \
    OrderPaymentSerializer, ShippingMethodSerializer, DeliverySerializer, UserSerializer, TaxSerializer, \
    StoreAdminSerializer, CategorySerializer


class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username']
    http_method_names = ['get', 'post', 'head', 'put']

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save()
        email = Email()
        email.subject = "Welcome to Grocery 60 !!!"
        email.email = serializer.data.get('email')
        email.first_name = serializer.data.get('first_name')
        email.username = serializer.data.get('username')
        email_send.send_email(email, 'registration.html')


class CartViewset(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id']


class CartItemViewset(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cart_id']

    def create(self, request):
        data = JSONParser().parse(request)
        product = Product.objects.get(id=data.get('product_id'))
        cart = Cart.objects.get(id=data.get('cart_id'))
        data['product_id'] = product.id
        data['cart_id'] = cart.id
        CartItem.objects.create(product_id=product.id, extra=data.get('extra'),
                                quantity=data.get('quantity'), cart_id=cart.id)
        return JsonResponse(data)

    def list(self, request):
        print('enter get')
        cart_id = request.GET.get('cart_id')
        cart = Cart.objects.get(id=cart_id)
        cart_item = CartItem.objects.select_related('product').all().filter(cart_id=cart_id). \
            order_by('product_id')
        print(cart_item.query)
        cart_item_list = []
        cart_item_dict = {}
        for item in cart_item:
            _dict = {}
            product_id_list = [_item['product_id'] for _item in cart_item_list]
            if item.product.id in product_id_list:
                _item = [_item for _item in cart_item_list if _item['product_id'] == item.product.id]
                cart_item_list.remove(_item[0])
                _dict['cart_item_id'] = item.id
                _dict['cart_id'] = item.cart.id
                _dict['product_id'] = item.product.id
                _dict['product_name'] = item.product.product_name
                _dict['product_url'] = item.product.product_url
                _dict['image'] = base64.b64encode(item.product.image).decode()
                _dict['price'] = item.product.price
                _dict['tax_exempt'] = item.product.tax_exempt
                _dict['quantity'] = _item[0]['quantity'] + item.quantity
                _dict['line_total'] = Decimal(_dict['quantity']) * Decimal(_dict['price'])
                cents = Decimal('.01')
                _dict['line_total'] = _dict['line_total'].quantize(cents, decimal.ROUND_HALF_UP)
                cart_item_list.append(_dict)
            else:
                _dict['cart_item_id'] = item.id
                _dict['cart_id'] = item.cart.id
                _dict['product_id'] = item.product.id
                _dict['product_name'] = item.product.product_name
                _dict['product_url'] = item.product.product_url
                _dict['image'] = base64.b64encode(item.product.image).decode()
                _dict['price'] = item.product.price
                _dict['tax_exempt'] = item.product.tax_exempt
                _dict['quantity'] = item.quantity
                _dict['line_total'] = Decimal(_dict['quantity']) * Decimal(_dict['price'])
                cents = Decimal('.01')
                _dict['line_total'] = _dict['line_total'].quantize(cents, decimal.ROUND_HALF_UP)
                cart_item_list.append(_dict)
            cart_item_dict = {'count': len(cart_item_list), 'results': cart_item_list}
        return JsonResponse(cart_item_dict, safe=False)


class CustomerViewset(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id']
    http_method_names = ['get', 'post', 'head', 'put']

    def create(self, request):
        data = JSONParser().parse(request)
        user = User.objects.get(id=data.get('customer_id'))
        data['customer_id'] = user.id
        Customer.objects.create(customer_id=user.id, last_access=data.get('last_access'),
                                extra=data.get('extra'), salutation=data.get('salutation'),
                                phone_number=data.get('phone_number'))
        return JsonResponse(data)

    def update(self, request, pk):
        data = JSONParser().parse(request)
        customer = Customer.objects.get(pk=pk)
        customer.salutation = data.get('salutation')
        customer.last_access = data.get('last_access')
        customer.extra = data.get('extra')
        customer.phone_number = data.get('phone_number')
        customer.save()
        serializer = CustomerSerializer(customer)
        return JsonResponse(serializer.data)


class CatalogViewset(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = CatalogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product_category', 'store_id', 'status']
    http_method_names = ['get', 'post', 'head', 'put']

    '''Allows bulk creation of a products.'''

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(CatalogViewset, self).get_serializer(*args, **kwargs)

    def perform_create(self, serializer):

        if serializer.is_valid():
            serializer.save()

            if isinstance(serializer.data, list):
                data = serializer.data[:]
            else:
                data = [serializer.data]

            for product in data:
                # Create Product
                store_id = str(product.get('store')) # Product Set creates using store id
                product_id = str(product.get('id'))
                search_product.create_product(settings.PROJECT, settings.REGION, product_id,
                                              product.get('product_name'),
                                              'homegoods')
                print(' Product created with product id ', product_id)
                # Create Product Image
                gcs_uri = str(product.get('product_url'))
                gcs_uri = gcs_uri.replace('https', 'gs')
                gcs_uri = gcs_uri.replace(settings.GS_BUCKET_NAME, settings.GS_BUCKET_NAME + '-ml')
                gcs_uri = gcs_uri.replace('storage.googleapis.com/', '')
                url_split = gcs_uri.split('/')
                reference_image_id = 'I_' + url_split[3]
                source_bucket = settings.GS_BUCKET_NAME
                source_object = url_split[3]
                destination_bucket = settings.GS_BUCKET_NAME + '-ml'

                client = storage.Client(project=settings.PROJECT)
                bucket = client.bucket(source_bucket)
                dst_bucket = client.bucket(destination_bucket)
                blob = bucket.blob(source_object)
                new_blob = bucket.copy_blob(blob, dst_bucket)
                new_blob.acl.save(blob.acl)

                search_product.create_reference_image(settings.PROJECT, settings.REGION, product_id,
                                                      reference_image_id,
                                                      gcs_uri)
                print(' Product created with product id ', product_id, 'reference_image_id ', reference_image_id)


                # Attach product to product set
                search_product.add_product_to_product_set(settings.PROJECT, settings.REGION, product_id,
                                                          'PS_'+store_id)
                print(' Added  in Product Set PS_' + store_id)

    '''Don't support bulk update'''

    def update(self, request, pk):
        serializer = CatalogSerializer(data=request.data)
        product = None
        if serializer.is_valid():
            product = Product.objects.get(id=pk)
            product.product_name = serializer.validated_data.get('product_name')
            product.product_url = serializer.validated_data.get('product_url') if serializer.validated_data.get(
                'product_url') else product.product_url
            product.product_category = serializer.validated_data.get('product_category')
            product.price = serializer.validated_data.get('price')
            product.media = serializer.validated_data.get('media')
            product.caption = serializer.validated_data.get('caption')
            product.status = serializer.validated_data.get('status')
            product.tax_exempt = serializer.validated_data.get('tax_exempt')
            product.store = serializer.validated_data.get('store')
            if serializer.validated_data.get('image'):
                product.image = serializer.validated_data.get('image')
            else:
                product.image = ContentFile(product.image)
            product.extra = serializer.validated_data.get('extra') if serializer.validated_data.get(
                'extra') else product.extra
            product.media = serializer.validated_data.get('media') if serializer.validated_data.get(
                'media') else product.media
            product.save()
            serializer = CatalogSerializer(product)

            return JsonResponse(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreAdminViewset(viewsets.ModelViewSet):
    queryset = StoreAdmin.objects.all()
    serializer_class = StoreAdminSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['store_id', 'username', 'status']
    http_method_names = ['get', 'post', 'head', 'put']

    def perform_create(self, serializer):
        if serializer.is_valid():
            text_password = util.generate_password(8)
            password = hashers.make_password(text_password)
            serializer.save(password=password)
            email = Email()
            email.subject = "Welcome to Grocery 60 !!!"
            email.email = serializer.data.get('email')
            email.username = serializer.data.get('username')
            email.password = text_password
            email_send.send_email(email, 'storeadmin_registration.html')


class StoreViewset(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['zip', 'nearby_zip', 'status']
    http_method_names = ['get', 'post', 'head', 'put']

    '''Allows bulk creation of a store.'''

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(StoreViewset, self).get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        print("Bulk Insert")
        if serializer.is_valid():
            serializer.save()
            if isinstance(serializer.data, list):
                data = serializer.data[:]
            else:
                data = [serializer.data]

            for store in data:
                # Create Product Set for Store
                product_set = 'PS_' + str(store.get('id'))
                product_set_display = product_set + ' Store Set'
                search_product.create_product_set(settings.PROJECT, settings.REGION, product_set, product_set_display)


    '''Don't support bulk update'''

    def update(self, request, pk):
        serializer = StoreSerializer(data=request.data)
        store = None
        if serializer.is_valid():
            store = Store.objects.get(id=pk)
            store.name = serializer.validated_data.get('name')
            store.address = serializer.validated_data.get('address')
            store.city = serializer.validated_data.get('city')
            store.state = serializer.validated_data.get('state')
            store.zip = serializer.validated_data.get('zip')
            store.nearby_zip = serializer.validated_data.get('nearby_zip')
            store.country = serializer.validated_data.get('country')
            store.store_url = serializer.validated_data.get('store_url') if serializer.validated_data.get('store_url') \
                else store.store_url
            store.phone = serializer.validated_data.get('phone')
            store.email = serializer.validated_data.get('email')
            store.status = serializer.validated_data.get('status')
            store.payment_account = serializer.validated_data.get('payment_account') if serializer.validated_data.get(
                'payment_account') \
                else store.payment_account
            if serializer.validated_data.get('image'):
                store.image = serializer.validated_data.get('image')
            else:
                store.image = ContentFile(store.image)
            store.media = serializer.validated_data.get('store_url') if serializer.validated_data.get('store_url') \
                else store.store_url
            store.save()
            serializer = StoreSerializer(store)
            return JsonResponse(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BillingAddressViewset(viewsets.ModelViewSet):
    queryset = BillingAddress.objects.all()
    serializer_class = BillingAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id', 'state']
    http_method_names = ['get', 'post', 'head', 'put']


class ShippingAddressViewset(viewsets.ModelViewSet):
    queryset = ShippingAddress.objects.all()
    serializer_class = ShippingAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id', 'state']
    http_method_names = ['get', 'post', 'head', 'put']


class OrderViewset(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id', 'status']
    http_method_names = ['get', 'post', 'head', 'put']


class OrderItemViewset(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id']
    http_method_names = ['get', 'post', 'head', 'put']

    def create(self, request):
        data_list = JSONParser().parse(request)

        for data in data_list:
            print(data)
            product = Product.objects.get(id=data.get('product_id'))
            order = Order.objects.get(id=data.get('order_id'))
            cents = Decimal('.01')
            line_total = product.price * Decimal(data.get('quantity'))
            line_total = line_total.quantize(cents, decimal.ROUND_HALF_UP)
            OrderItem.objects.create(product_id=product.id, order_id=order.id, extra=data.get('extra'),
                                     line_total=line_total,
                                     quantity=data.get('quantity'), canceled=data.get('canceled'))
        return JsonResponse(data_list, safe=False)


class OrderPaymentViewset(viewsets.ModelViewSet):
    queryset = OrderPayment.objects.all().order_by('-id')
    serializer_class = OrderPaymentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id', 'store_id', 'status', 'payout_status', 'payout_message']
    http_method_names = ['get', 'post', 'head', 'put']

    def update(self, request, pk):
        order_payment = OrderPayment.objects.get(id=pk)
        data = JSONParser().parse(request)
        if data.get('amount'):
            order_payment.amount = data.get('amount')
        if data.get('transaction_id'):
            order_payment.transaction_id = data.get('transaction_id')
        if data.get('status'):
            order_payment.status = data.get('status')
            if data.get('status') == "PICKED":
                order_payment.payout_status = "READY_TO_PAY"
        if data.get('payment_method'):
            order_payment.payment_method = data.get('payment_method')
        if data.get('order'):
            order_payment.order.id = data.get('order')
        if data.get('store'):
            order_payment.store.id = data.get('store')
        if data.get('payout_message'):
            order_payment.payout_message = data.get('payout_message')
        if data.get('payout_status'):
            order_payment.payout_status = data.get('payout_status')
        if data.get('payout_message'):
            order_payment.payout_id = data.get('payout_id')
        order_payment.save()
        serializer = OrderPaymentSerializer(order_payment)
        if data.get('status') == "READY_TO_PICK":
            recipient_email = Email()
            recipient_email.subject = "Order Ready to pick up for Grocery 60"
            user = User.objects.get(id=order_payment.order.customer_id)
            recipient_email.email = user.email
            recipient_email.order_id = order_payment.order_id
            order_payment.send_pickup_email(recipient_email)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)


class ShippingMethodViewset(viewsets.ModelViewSet):
    queryset = ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer
    filter_backends = [DjangoFilterBackend]
    http_method_names = ['get', 'post', 'head', 'put']


class DeliveryViewset(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id']
    http_method_names = ['get', 'post', 'head', 'put']


class TaxViewset(viewsets.ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['state','country']
    http_method_names = ['get', 'post', 'head', 'put']

    def retrieve(self, request, pk=None):
        queryset = Tax.objects.all().distinct('country').values('country')
        return JsonResponse(list(queryset), safe=False)


class CategoryViewset(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    http_method_names = ['get', 'post', 'head', 'put']
