import graphene
from graphene_django.types import DjangoObjectType
from rest_framework.decorators import authentication_classes, permission_classes

from grocery60_be.models import Store


class StoreType(DjangoObjectType):
    class Meta:
        model = Store
        fields = '__all__'

@authentication_classes([])
@permission_classes([])
class Query:
    stores = graphene.List(StoreType)
    store = graphene.Field(StoreType, id=graphene.String())

    def resolve_stores(self, info, **kwargs):
        # Querying a list
        return Store.objects.all()

    def resolve_store(self, info, id):
        # Querying a single question
        return Store.objects.get(pk=id)