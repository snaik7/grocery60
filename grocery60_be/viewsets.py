from rest_framework import viewsets
from . import models
from . import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

class CartViewset(viewsets.ModelViewSet):
    queryset = models.Cart.objects.all()
    serializer_class = serializers.CartSerializer

class CustomerViewset(viewsets.ModelViewSet):
    queryset = models.Customer.objects.all()
    serializer_class = serializers.CustomerSerializer

class CatalogViewset(viewsets.ModelViewSet):
    queryset = models.Product.objects.all()
    serializer_class = serializers.CatalogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product_category', 'store_id']

class StoreViewset(viewsets.ModelViewSet):
    queryset = models.Store.objects.all()
    serializer_class = serializers.StoreSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['zip','nearby_zip']

class BillingAddressViewset(viewsets.ModelViewSet):
    queryset = models.BillingAddress.objects.all()
    serializer_class = serializers.BillingAddressSerializer

class ShippingAddressViewset(viewsets.ModelViewSet):
    queryset = models.ShippingAddress.objects.all()
    serializer_class = serializers.ShippingAddressSerializer


class OrderViewset(viewsets.ModelViewSet):
    queryset = models.Order.objects.all()
    serializer_class = serializers.OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer_id','status']

class OrderItemViewset(viewsets.ModelViewSet):
    queryset = models.OrderItem.objects.all()
    serializer_class = serializers.OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id']

class OrderPaymentViewset(viewsets.ModelViewSet):
    queryset = models.OrderPayment.objects.all()
    serializer_class = serializers.OrderPaymentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id']

class ShippingMethodViewset(viewsets.ModelViewSet):
    queryset = models.ShippingMethod.objects.all()
    serializer_class = serializers.ShippingMethodSerializer
    filter_backends = [DjangoFilterBackend]

class DeliveryViewset(viewsets.ModelViewSet):
    queryset = models.Delivery.objects.all()
    serializer_class = serializers.DeliverySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_id']
