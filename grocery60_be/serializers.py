from django.contrib.auth.models import User, Group
from rest_framework import serializers
from grocery60_be.models import Store, Product, Customer, Cart

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class StoreSerializer(serializers.ModelSerializer):
	    class Meta:
	        db_table = 'store'
	        model = Store
	        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
	    class Meta:
	        db_table = 'customer'
	        model = Customer
	        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
	    class Meta:
	        db_table = 'cart'
	        model = Cart
	        fields = '__all__'

class CatalogSerializer(serializers.ModelSerializer):
	    class Meta:
	        db_table = 'product'
	        model = Product
	        fields = '__all__'


        