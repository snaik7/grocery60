import graphene
from graphene_django.types import DjangoObjectType
from rest_framework.decorators import authentication_classes, permission_classes

from grocery60_be.models import Store, Product


class StoreType(DjangoObjectType):
    class Meta:
        model = Store
        fields = '__all__'


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


@authentication_classes([])
@permission_classes([])
class Query:
    stores = graphene.List(StoreType)
    store = graphene.Field(StoreType, id=graphene.String())
    store_search = graphene.List(StoreType, store_name=graphene.String())

    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.String())
    product_search = graphene.List(ProductType, category=graphene.String(), product_name=graphene.String(),
                                   extra=graphene.String(), store_id=graphene.Int())


    def resolve_stores(self, info, **kwargs):
        # Querying a list
        return Store.objects.all()

    def resolve_store(self, info, id):
        # Querying a single question
        return Store.objects.get(pk=id)

    def resolve_store_search(self, info, **kwargs):
        store_name = kwargs.get("store_name", "")
        return Store.objects.filter(name__icontains=store_name)

    def resolve_products(self, info, **kwargs):
        # Querying a list
        return Product.objects.all()

    def resolve_product(self, info, id):
        # Querying a list
        return Product.objects.get(pk=id)


    def resolve_product_search(self, info, **kwargs):
        category = kwargs.get("category", "")
        product_name = kwargs.get("product_name", "")
        extra = kwargs.get("extra", "")
        store_id = kwargs.get("store_id", 0)
        return Product.objects.filter(product_category__icontains=category, product_name__icontains=product_name, extra__icontains=extra, store=store_id)
