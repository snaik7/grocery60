import graphene
from django.db.models import Count
from graphql import GraphQLError
from graphene_django.types import DjangoObjectType

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
    store = graphene.Field(StoreType, id=graphene.String(), token=graphene.String())
    store_search = graphene.List(StoreType, store_name=graphene.String(), first=graphene.Int(), skip=graphene.Int(),
                                 token=graphene.String())

    products = graphene.List(ProductType, first=graphene.Int(), skip=graphene.Int(), token=graphene.String())
    product = graphene.Field(ProductType, id=graphene.String(), token=graphene.String())
    product_search = graphene.List(ProductType, category=graphene.String(), product_name=graphene.String(),
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
            raise GraphQLError('Authentication credentials were not provided')

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
            raise GraphQLError('Authentication credentials were not provided')

    def resolve_store(self, info, id, token=None, ):
        if validate_token(token):
            # Querying a single question
            return Store.objects.get(pk=id)
        else:
            raise GraphQLError('Authentication credentials were not provided')

    def resolve_store_search(self, info, first=None, skip=None, token=None, **kwargs):
        if validate_token(token):
            store_name = kwargs.get("store_name", "")
            qs = Store.objects.filter(name__icontains=store_name, status='ACTIVE')
            if skip:
                qs = qs[skip:]
            if first:
                qs = qs[:first]
            return qs
        else:
            raise GraphQLError('Authentication credentials were not provided')

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
            raise GraphQLError('Authentication credentials were not provided')

    def resolve_product(self, info, id, token=None):
        if validate_token(token):
            # Querying a list
            return Product.objects.get(pk=id)
        else:
            raise GraphQLError('Authentication credentials were not provided')

    def resolve_product_search(self, info, first=None, skip=None, token=None, **kwargs):
        if validate_token(token):
            category = kwargs.get("category", "")
            product_name = kwargs.get("product_name", "")
            extra = kwargs.get("extra", "")
            store_id = kwargs.get("store_id", 0)
            qs = Product.objects.filter(product_category__icontains=category, product_name__icontains=product_name,
                                        extra__icontains=extra, store=store_id, status='ACTIVE')
            if skip:
                qs = qs[skip:]
            if first:
                qs = qs[:first]
            return qs
        else:
            raise GraphQLError('Authentication credentials were not provided')
