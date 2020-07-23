from graphene import ObjectType, Schema
from grocery60_be.graphql.schema import Query



class Query(Query, ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = Schema(query=Query)
#schema = Schema(query=Query, mutation=Mutation)
