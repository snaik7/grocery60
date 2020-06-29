from rest_framework import viewsets
from . import models
from . import serializers
from grocery60_be.models import Order, OrderPayment
from rest_framework.response import Response
import stripe 
from rest_framework.views import APIView
from django.http import JsonResponse
import json
from rest_framework.parsers import JSONParser
from django.db import connection
from datetime import datetime

class CustomerPaymentView(viewsets.ViewSet):
    def get(self, request, customer_id):
        query_set = OrderPayment.objects.select_related('order').filter(order__customer_id=customer_id)
        serializer = serializers.OrderPaymentSerializer(query_set, many=True)
        return Response(serializer.data)


class PaymentView(APIView):
    def post(self,request):
        try:
            data = JSONParser().parse(request)
            intent = stripe.PaymentIntent.create(
                amount = data.get('amount'),
                currency = data.get('currency'),
                receipt_email = data.get('receipt_email'),
                confirmation_method = 'automatic',
                payment_method_data = {
                      "type" : "card",
                       "card" : {
                        "number": data.get('card').get('number'),
                        "exp_month": data.get('card').get('exp_month'),
                        "exp_year": data.get('card').get('exp_year'),
                        "cvc": data.get('card').get('cvc')
                      },
                    "billing_details" : {
                        "address": {
                          "city": data.get('billing_details').get('address').get('city'),
                          "country": data.get('billing_details').get('address').get('country'),
                          "line1": data.get('billing_details').get('address').get('line1'),
                          "line2": data.get('billing_details').get('address').get('line2'),
                          "postal_code": data.get('billing_details').get('address').get('postal_code'),
                          "state": data.get('billing_details').get('address').get('state'),
                        },
                  
                      }
                },
                metadata = {
                    "OrderId": data.get('metadata').get('order_id'),
                    "Phone": data.get('metadata').get('phone'),
                    "CustomerId": data.get('metadata').get('customer_id')

                }
            )

            intent = stripe.PaymentIntent.retrieve(
              intent.get('id')
            )
            
            if record_payment(data,intent) == 1: 
                return JsonResponse(intent)
            else:
                raise Exception('Order Payment failed for Order = '+ order_id)
            
        except Exception as e:
            response_dict = {
            'status': 'error',
            # the format of error message determined by you base exception class
            'msg': str(e)
            }
            return JsonResponse(response_dict,status=403)

class PaymentWebhookView(APIView):    
    def post(self,request):
        payload = JSONParser().parse(request)
        #payload = request.get_data()
        #sig_header = request.headers.get('STRIPE_SIGNATURE')
        sig_header = request.META.get('STRIPE_SIGNATURE')
        event = None
        endpoint_secret = 'we_1GzJNB2eZvKYlo2CMyWT8lZu'
        print('here 0')
        try:
            event = stripe.Webhook.construct_event(
              payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # invalid payload
            response_dict = {'status': 'Invalid payload'}
            return JsonResponse(response_dict,status=400)
        except stripe.error.SignatureVerificationError as e:
            # invalid signature
            response_dict = {'status': 'Invalid signature'}
            return JsonResponse(response_dict,status=400)
        event_dict = event.to_dict()
        if event_dict['type'] == "payment_intent.succeeded":
            intent = event_dict['data']['object']
            print("Succeeded: ", intent['id'])
            # Fulfill the customer's purchase
        elif event_dict['type'] == "payment_intent.payment_failed":
            intent = event_dict['data']['object']
            error_message = intent['last_payment_error']['message'] if intent.get('last_payment_error') else None
            print("Failed: ", intent['id'], error_message)
            # Notify the customer that payment failed
        update_payment(intent['id'],event_dict['type'])
        print("Database Update Succeeded: ", intent['id'])
        return JsonResponse(event_dict,status=403)


def record_payment(data,intent):
    amount = data.get('amount') 
    transaction_id = intent.get('id')
    payment_method = 'card'
    order_id = data.get('metadata').get('order_id')
    status = intent.get('status') 
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO orderpayment(amount, transaction_id, payment_method, order_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",[amount,transaction_id,payment_method,order_id,status,datetime.now(), datetime.now() ])
    return cursor.rowcount

def update_payment(transaction_id,status):
    with connection.cursor() as cursor:
        cursor.execute("update orderpayment set status =%s, updated_at=%s where transaction_id=%s ",[amount,transaction_id,payment_method,order_id,status,datetime.now(), datetime.now() ])
    return cursor.rowcount

