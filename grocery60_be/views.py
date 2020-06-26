from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
import traceback
from grocery60_be.models import Store
from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from . import serializers

'''
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer(queryset, many=True)
'''

'''
class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
'''

from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


class StoreView(APIView):

    def get(self, request):
        try:
            queryset = Store.objects.all()
            store_list = []
            for store in queryset:
                __ = {}
                __['name'] = store.name
                __['address'] = store.address
                __['city'] = store.city
                __['zip'] = store.zip
                store_list.append(__)
            return JsonResponse(store_list, safe=False)

        except Exception as e:
            track = traceback.format_exc()
            print(track)
            response_dict = {
                'status': 'error',
                # the format of error message determined by you base exception class
                'msg': str(e)
            }
            return JsonResponse(response_dict, status=500)
