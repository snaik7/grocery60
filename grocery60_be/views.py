from rest_framework import viewsets
from . import models
from . import serializers
from grocery60_be.models import Order, OrderPayment
from rest_framework.response import Response

class CustomerPaymentView(viewsets.ViewSet):
    def get(self, request, customer_id):
        query_set = OrderPayment.objects.select_related('order').filter(order__customer_id=customer_id)
        serializer = serializers.OrderPaymentSerializer(query_set, many=True)
        return Response(serializer.data)


