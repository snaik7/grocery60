import asyncio
import base64
import decimal
from decimal import Decimal

from django.contrib.auth import hashers
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models import Count
from rest_framework import viewsets, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import JSONParser
from django.http import JsonResponse
from grocery60_be import email as email_send

from grocery60_be.error import ValidationError
from grocery60_be.models import Cart, CartItem, Customer, Product, Store, BillingAddress, ShippingAddress, Order, \
    OrderItem, OrderPayment, ShippingMethod, Delivery, Tax, Email, StoreAdmin
from grocery60_be.serializers import CartSerializer, CartItemSerializer, CustomerSerializer, CatalogSerializer, \
    StoreSerializer, BillingAddressSerializer, ShippingAddressSerializer, OrderSerializer, OrderItemSerializer, \
    OrderPaymentSerializer, ShippingMethodSerializer, DeliverySerializer, UserSerializer, TaxSerializer, \
    StoreAdminSerializer


class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username']

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save()
        email = Email()
        email.subject = "Welcome to Grocery 60 !!!"
        email.email = serializer.data.get('email')
        email.first_name = serializer.data.get('first_name')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(email_send.send_email(email, 'registration.html'))


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
            annotate(total=Count('product_id')).order_by('product_id')
        print(cart_item.query)
        cart_item_list = []
        count = 0
        line_total = Decimal(0)
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
        return JsonResponse(cart_item_list, safe=False)


class CustomerViewset(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id']

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
    filterset_fields = ['product_category', 'store_id']

    '''Allows bulk creation of a products.'''

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(CatalogViewset, self).get_serializer(*args, **kwargs)

    '''Don't support bulk update'''

    def update(self, request, pk):
        serializer = CatalogSerializer(data=request.data)
        product = None
        if serializer.is_valid():
            product = Product.objects.get(id=pk)
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
    filterset_fields = ['store_id', 'username']

    def perform_create(self, serializer):
        if serializer.is_valid():
            password = hashers.make_password(serializer.validated_data.get('password'))
            serializer.save(password=password)


class StoreViewset(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['zip', 'nearby_zip']

    '''Allows bulk creation of a store.'''

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(StoreViewset, self).get_serializer(*args, **kwargs)

    '''Don't support bulk update'''

    def update(self, request, pk):
        serializer = StoreSerializer(data=request.data)
        store = None
        if serializer.is_valid():
            store = Store.objects.get(id=pk)
            if serializer.validated_data.get('image'):
                store.image = serializer.validated_data.get('image')
            else:
                store.image = ContentFile(store.image)
            store.media = serializer.validated_data.get('store_url') if serializer.validated_data.get('store_url') \
                else store.store_url
            store.save()
            serializer = CatalogSerializer(store)
            return JsonResponse(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BillingAddressViewset(viewsets.ModelViewSet):
    queryset = BillingAddress.objects.all()
    serializer_class = BillingAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id', 'state']


class ShippingAddressViewset(viewsets.ModelViewSet):
    queryset = ShippingAddress.objects.all()
    serializer_class = ShippingAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id', 'state']



class OrderViewset(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id', 'status']


class OrderItemViewset(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id']

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
    queryset = OrderPayment.objects.all()
    serializer_class = OrderPaymentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id', 'store_id']


class ShippingMethodViewset(viewsets.ModelViewSet):
    queryset = ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer
    filter_backends = [DjangoFilterBackend]


class DeliveryViewset(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id']


class TaxViewset(viewsets.ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['state']
