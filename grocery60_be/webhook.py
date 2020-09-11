from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from grocery60_be.models import OrderPayment


# Stripe can make webhook call without auth
@authentication_classes([])
@permission_classes([])
class PaymentWebhookView(APIView):
    def post(self, request):
        payload = JSONParser().parse(request)
        event_dict = payload
        print('Webhook Payload from Stripe ', event_dict['data']['object'], '  ', event_dict['type'])
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
            print('Webhook Payload from Stripe ', payload)
            intent = event_dict['data']['object']
            print("No action unknown event : ", intent['id'], '   ', event_dict['type'])

        payment_status = None
        if event_dict['type'] == "payment_intent.succeeded":
            payment_status = "SUCCEEDED"
            OrderPayment().update_payment(intent['id'], payment_status)
        if event_dict['type'] == "payment_intent.payment_failed":
            payment_status = "FAILED"
            OrderPayment().update_payment(intent['id'], payment_status)

        print("Database Update Succeeded: ", intent['id'], ' status ', payment_status)

        return JsonResponse(event_dict, status=status.HTTP_200_OK)
