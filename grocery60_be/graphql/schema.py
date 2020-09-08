import graphene
from django.db.models import Count
from graphql import GraphQLError
from graphene_django.types import DjangoObjectType

from grocery60_be.error import ValidationError
from grocery60_be.models import Store, Product, CartItem, Cart
from grocery60_be.models import Count as CountModel
from grocery60_be import settings


class StoreType(DjangoObjectType):
    class Meta:
        model = Store
        fields = '__all__'


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


class CountType(DjangoObjectType):
    class Meta:
        model = CountModel
        fields = '__all__'


def validate_token(token):
    return settings.GRAPHQL_TOKEN == token


class Query:

    cart_item_count = graphene.Field(CountType, token=graphene.String(), customer_id=graphene.Int())

    stores = graphene.List(StoreType, first=graphene.Int(), skip=graphene.Int(), token=graphene.String())
    store = graphene.Field(StoreType, store_id=graphene.Int(), token=graphene.String())
    store_search = graphene.List(StoreType, store_name=graphene.String(), country=graphene.String(), first=graphene.Int(),
                                 skip=graphene.Int(), token=graphene.String())
    store_zip_search = graphene.List(StoreType, nearby_zip=graphene.String(), country=graphene.String(),
                                     first=graphene.Int(), skip=graphene.Int(), token=graphene.String())

    products = graphene.List(ProductType, first=graphene.Int(), skip=graphene.Int(), token=graphene.String())
    product = graphene.Field(ProductType, product_id=graphene.Int(), token=graphene.String())
    product_search = graphene.List(ProductType, product_category=graphene.String(), product_name=graphene.String(),
                                   extra=graphene.String(), store_id=graphene.Int(), first=graphene.Int(),
                                   skip=graphene.Int(), token=graphene.String())

    def resolve_cart_item_count(self, info, token=None, **kwargs):
        if validate_token(token):
            customer_id = kwargs.get("customer_id")
            cart = Cart.objects.get(customer_id=customer_id)
            cart_item = CartItem.objects.select_related('product').filter(cart_id=cart.id) \
                .aggregate(count=Count('product_id', distinct=True))
            count = CountType()
            count.count = cart_item.get('count')
            return count
        else:
            raise ValidationError('Authentication credentials were not provided')

    def resolve_stores(self, info, first=None, skip=None, token=None, **kwargs):
        if validate_token(token):
            # Querying a list
            qs = Store.objects.filter(status='ACTIVE')
            if skip:
                qs = qs[skip:]
            if first:
                qs = qs[:first]
            return qs
        else:
            raise ValidationError('Authentication credentials were not provided')

    def resolve_store(self, info, store_id, token=None, ):
        if validate_token(token):
            # Querying a single question
            return Store.objects.get(store_id=store_id)
        else:
            raise ValidationError('Authentication credentials were not provided')

    def resolve_store_search(self, info, first=None, skip=None, token=None, **kwargs):
        if validate_token(token):
            store_name = kwargs.get("store_name", "")
            country = kwargs.get("country", "USA")
            qs = Store.objects.filter(name__icontains=store_name, country=country, status='ACTIVE')
            if skip:
                qs = qs[skip:]
            if first:
                qs = qs[:first]
            return qs
        else:
            raise ValidationError('Authentication credentials were not provided')

    def resolve_store_zip_search(self, info, first=None, skip=None, token=None, **kwargs):
        if validate_token(token):
            nearby_zip = kwargs.get("nearby_zip", "")
            country = kwargs.get("country", "USA")
            qs = Store.objects.filter(nearby_zip__icontains=nearby_zip, country=country, status='ACTIVE')
            if skip:
                qs = qs[skip:]
            if first:
                qs = qs[:first]
            return qs
        else:
            raise ValidationError('Authentication credentials were not provided')



    def resolve_products(self, info, first=None, skip=None, token=None, **kwargs):
        if validate_token(token):
            # Querying a list
            qs = Product.objects.filter(status='ACTIVE')
            if skip:
                qs = qs[skip:]
            if first:
                qs = qs[:first]
            return qs
        else:
            raise ValidationError('Authentication credentials were not provided')

    def resolve_product(self, info, product_id, token=None):
        if validate_token(token):
            # Querying a list
            return Product.objects.get(product_id=product_id)
        else:
            raise ValidationError('Authentication credentials were not provided')

    def resolve_product_search(self, info, first=None, skip=None, token=None, **kwargs):
        if validate_token(token):

            _kwargs = {}
            if kwargs.get('product_category') is not None:
                _kwargs['product_category__icontains'] = kwargs.get('product_category')

            if kwargs.get('product_name') is not None:
                _kwargs['product_name__icontains'] = kwargs.get('product_name')

            if kwargs.get('extra') is not None:
                _kwargs['extra__icontains'] = kwargs.get('extra')

            if kwargs.get('store_id') is not None:
                _kwargs['store_id'] = kwargs.get('store_id')

            qs = Product.objects.filter(status='ACTIVE', **_kwargs)

            if skip:
                qs = qs[skip:]
            if first:
                qs = qs[:first]
            return qs
        else:
            raise ValidationError('Authentication credentials were not provided')
