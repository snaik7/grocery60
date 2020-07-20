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
    store_search = graphene.List(StoreType, string=graphene.String())

    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.String())
    product_category = graphene.List(ProductType, category=graphene.String(), product_name=graphene.String(),store_id=graphene.Int())
    product_search = graphene.List(ProductType, string=graphene.String())

    def resolve_stores(self, info, **kwargs):
        # Querying a list
        return Store.objects.all()

    def resolve_store(self, info, id):
        # Querying a single question
        return Store.objects.get(pk=id)

    def resolve_store_search(self, info, **kwargs):
        string = kwargs.get("string", "")
        return Store.objects.filter(name__icontains=string)

    def resolve_products(self, info, **kwargs):
        # Querying a list
        return Product.objects.all()

    def resolve_product(self, info, id):
        # Querying a list
        return Product.objects.get(pk=id)

    def resolve_product_search(self, info, **kwargs):
        string = kwargs.get("string", "")
        return Product.objects.filter(product_name__icontains=string)

    def resolve_product_category(self, info, **kwargs):
        category = kwargs.get("category", "")
        product_name = kwargs.get("product_name", "")
        store_id = kwargs.get("store_id",0)
        print(store_id)
        return Product.objects.filter(product_category__icontains=category,product_name__icontains=product_name, store=store_id)
