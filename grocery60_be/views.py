import asyncio
import decimal
import traceback
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes

from grocery60_be import serializers, models
from grocery60_be.models import OrderPayment, Email, BillingAddress, Customer
import stripe
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_auth.views import LoginView
from grocery60_be import email as email_send


class FeeCalView(APIView):
    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        sub_total = data.get('sub_total')
        no_tax_total = data.get('no_tax_total')
        tip = data.get('tip')
        customer_id = data.get('customer_id')
        address = BillingAddress.objects.filter(customer_id=customer_id).first()
        print('state', address.state)
        cents = Decimal('.01')
        tip = Decimal(sub_total) * Decimal('0.05') if tip is None else Decimal(tip)
        tip = tip.quantize(cents, decimal.ROUND_HALF_UP)
        tax = Decimal(sub_total) * Decimal(models.get_tax(address.state) / 100)
        tax = tax.quantize(cents, decimal.ROUND_HALF_UP)
        sub_total = Decimal(sub_total) + Decimal(no_tax_total)
        sub_total = sub_total.quantize(cents, decimal.ROUND_HALF_UP)
        service_fee = models.get_service_fee(sub_total)
        discount = models.get_discount(customer_id, sub_total)
        total = Decimal(sub_total) + tax + tip + service_fee - discount
        total = total.quantize(cents, decimal.ROUND_HALF_UP)
        return Response({'sub_total': sub_total, 'tax': tax, 'tip': tip, 'service_fee': service_fee,
                        'discount': discount,'total': total})


class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data.get('key'))
        return Response({'token': token.key, 'id': token.user_id})


class CustomerPaymentView(APIView):
    def get(self, request, customer_id):
        query_set = OrderPayment.objects.select_related('order').filter(order__customer_id=customer_id)
        serializer = serializers.OrderPaymentSerializer(query_set, many=True)
        return JsonResponse(serializer.data, safe=False)


class CatalogSearchView(APIView):
    def get(self, request):
        search_key = request.GET.get('search_key')
        store_id = request.GET.get('store_id')
        print(store_id)
        dict, status = models.Product().search_catalog(search_key, store_id)
        return JsonResponse(dict, status=status, safe=False)


class PaymentView(APIView):

    def delete(self, request, order_id):
        print('order id cancellation', order_id)
        order_payment = OrderPayment.objects.filter(order_id=order_id).first()
        print(order_payment.transaction_id)
        try:
            # To cancel a PaymentIntent
            intent = stripe.PaymentIntent.cancel(
                order_payment.transaction_id)
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            raise Exception('Order Cancellation failed for Order  #{:d}. Please email to info@grocery60.online '
                            'and we will reply you in 24 hours. '.format(order_id))

        if intent.get('status') == 'canceled':
            order_payment.status = 'Cancelled'
            order_payment.save()
            # Send email for order cancellation
            email = Email()
            email.subject = "Order cancellation for Grocery 60"
            customer = Customer.objects.filter(customer_id=order_payment.order.customer_id).first()
            email.email = customer.email
            email.order_id = order_payment.order_id
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(email_send.send_email(email, 'order_cancellation.html'))
            return JsonResponse(data='',status=status.HTTP_204_NO_CONTENT, safe=False)
        else:
            raise Exception('Order Cancellation failed for Order = ', order_id)


    def post(self, request):
        data = JSONParser().parse(request)
        order_id = data.get('metadata').get('order_id')
        # view is not fat but payload is fat...sorry payment view
        intent = stripe.PaymentIntent.create(
            amount=data.get('amount') * 100,  # convert to cents
            currency=data.get('currency'),
            receipt_email=data.get('receipt_email'),
            confirmation_method='automatic',
            payment_method_data={
                "type": "card",
                "card": {
                    "number": data.get('card').get('number'),
                    "exp_month": data.get('card').get('exp_month'),
                    "exp_year": data.get('card').get('exp_year'),
                    "cvc": data.get('card').get('cvc')
                },
                "billing_details": {
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
            metadata={
                "OrderId": data.get('metadata').get('order_id'),
                "Phone": data.get('metadata').get('phone'),
                "CustomerId": data.get('metadata').get('customer_id')

            }
        )

        print('stripe.PaymentIntent.create success with intent ' + intent.get('id'))

        intent = stripe.PaymentIntent.retrieve(
            intent.get('id')
        )

        if OrderPayment().record_payment(data, intent):
            recipient_email = Email()
            recipient_email.subject = "Order Confirmation for Grocery 60"
            recipient_email.email = data.get('receipt_email')
            recipient_email.order_id = order_id
            recipient_email.set_order(order_id)
            order_payment = OrderPayment()
            order_payment.send_success_email(recipient_email)
            return JsonResponse(intent)
        else:
            raise Exception('Order Payment failed for Order = ' + order_id)


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

        if event_dict['type'] == "payment_intent.succeeded" or event_dict['type'] == "payment_intent.payment_failed":
            OrderPayment().update_payment(intent['id'], event_dict['type'])
            print("Database Update Succeeded: ", intent['id'])

        return JsonResponse(event_dict, status=status.HTTP_200_OK)