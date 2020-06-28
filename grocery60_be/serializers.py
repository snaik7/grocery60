from django.contrib.auth.models import User, Group
from rest_framework import serializers
from grocery60_be.models import Store, Product, Customer, Cart, BillingAddress, ShippingAddress, Order, OrderItem, OrderPayment, ShippingMethod, Delivery

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class StoreSerializer(serializers.ModelSerializer):
	        model = Store
	        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
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

class BillingAddressSerializer(serializers.ModelSerializer):
	    class Meta:
	        model = BillingAddress
	        fields = '__all__'

class ShippingAddressSerializer(serializers.ModelSerializer):
	    class Meta:
	        db_table = 'shippingaddress'
	        model = ShippingAddress
	        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
	    class Meta:
	        model = Order
	        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
	    class Meta:
	        model = OrderItem
	        fields = '__all__'

class OrderPaymentSerializer(serializers.ModelSerializer):
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
	        
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'mobile', 'password')

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


        