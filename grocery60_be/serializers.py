import decimal
from decimal import Decimal, getcontext

from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from grocery60_be.error import ValidationError
from grocery60_be.models import Store, Product, Customer, Cart, CartItem, BillingAddress, ShippingAddress, Order, \
    OrderItem, OrderPayment, ShippingMethod, Delivery, Tax, StoreAdmin, Category, User, Leads
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super(UserSerializer, self).create(validated_data)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'is_active', 'last_login', 'last_name', 'groups', 'password',
                  'verified']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'


class StoreAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreAdmin
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = '__all__'


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'


class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    product = CatalogSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'


class BillingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingAddress
        fields = '__all__'


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product = CatalogSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderPaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = OrderPayment
        fields = '__all__'


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = '__all__'


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = '__all__'


class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class LeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        fields = '__all__'
