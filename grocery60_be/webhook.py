from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from grocery60_be.models import OrderPayment

# Stripe can call without auth
@authentication_classes([])
@permission_classes([])
class PaymentWebhookView(APIView):
    def post(self, request):
        payload = JSONParser().parse(request)
        print('Webhook Payload from Stripe ', payload)
        event_dict = payload
        if event_dict['type'] == "payment_intent.succeeded":
            intent = event_dict['data']['object']
            print("Succeeded: ", intent['id'])
            # Fulfill the customer's purchase
            order_payment = OrderPayment()
            order_payment.send_store_email(intent['id'])
        elif event_dict['type'] == "payment_intent.payment_failed":
            intent = event_dict['data']['object']
            error_message = intent['last_payment_error']['message'] if intent.get('last_payment_error') else None
            print("Failed: ", intent['id'], error_message)
            # Notify the customer that payment failed
            order_payment = OrderPayment()
            order_payment.send_failure_email(intent['id'])
        else:
            intent = event_dict['data']['object']
            print("Update unknown event : ", intent['id'], '   ', event_dict['type'])

        payment_status = None
        if event_dict['type'] == "payment_intent.succeeded":
            payment_status = "SUCCESS"
        if event_dict['type'] == "payment_intent.payment_failed":
            payment_status = "FAIL"
        OrderPayment().update_payment(intent['id'], payment_status)
        print("Database Update Succeeded: ", intent['id'])

        return JsonResponse(event_dict, status=status.HTTP_200_OK)