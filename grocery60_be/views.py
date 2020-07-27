import asyncio
import decimal
from decimal import Decimal

from django.contrib.auth import hashers
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes

from grocery60_be import serializers, models, util, settings
from grocery60_be.models import OrderPayment, Email, BillingAddress, StoreAdmin, Order, Product, OrderItem
import stripe
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_auth.views import LoginView
from grocery60_be import email as email_send
from grocery60_be.serializers import OrderSerializer

import razorpay


class FeeCalView(APIView):
    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        sub_total = data.get('sub_total')
        no_tax_total = data.get('no_tax_total')
        tip = data.get('tip')
        shipping_id = data.get('shipping_id')
        custom_tip = data.get('custom_tip')
        customer_id = data.get('customer_id')
        address = BillingAddress.objects.filter(customer_id=customer_id).first()
        print('state', address.state)
        tip = models.get_tip(tip, custom_tip, sub_total)
        shipping_fee = models.get_shipping_cost(shipping_id) if shipping_id else Decimal('0')
        cents = Decimal('.01')
        tax = Decimal(sub_total) * Decimal(models.get_tax(address.state) / 100)
        tax = tax.quantize(cents, decimal.ROUND_HALF_UP)
        sub_total = Decimal(sub_total) + Decimal(no_tax_total)
        sub_total = sub_total.quantize(cents, decimal.ROUND_HALF_UP)
        service_fee = models.get_service_fee(sub_total)
        discount = models.get_discount(customer_id, sub_total)
        total = Decimal(sub_total) + tax + tip + service_fee + shipping_fee - discount
        total = total.quantize(cents, decimal.ROUND_HALF_UP)
        return Response({'sub_total': sub_total, 'tax': tax, 'tip': tip, 'service_fee': service_fee,
                         'shipping_fee': shipping_fee, 'discount': discount, 'total': total})


@authentication_classes([])
@permission_classes([])
class StoreLoginView(APIView):
    def post(self, request):
        data = JSONParser().parse(request)
        username = data.get('username')
        password = data.get('password')
        store_admin = StoreAdmin.objects.filter(username=username).first()
        valid = hashers.check_password(password, store_admin.password)
        if valid:
            data = {'message': 'success'}
            return JsonResponse(data=data, status=status.HTTP_200_OK, safe=False)
        else:
            data = {'message': 'failure'}
            return JsonResponse(data=data, status=status.HTTP_401_UNAUTHORIZED, safe=False)


@authentication_classes([])
@permission_classes([])
class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data.get('key'))
        return JsonResponse(data={'token': token.key, 'id': token.user_id}, status=status.HTTP_200_OK, safe=False)


class CustomerPaymentView(APIView):
    def get(self, request, customer_id):
        query_set = OrderPayment.objects.select_related('order').filter(order__customer_id=customer_id).order_by('-id')
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
            order_payment.status = 'CANCELLED'
            order_payment.save()
            order = Order.objects.get(id=order_id)
            order.status = 'CANCELLED'
            order.save()
            # Send email for order cancellation
            email = Email()
            email.subject = "Order cancellation for Grocery 60"
            user = User.objects.get(id=order_payment.order.customer_id)
            email.email = user.email
            email.order_id = order_payment.order_id
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(email_send.send_email(email, 'order_cancellation.html'))
            return JsonResponse(data='', status=status.HTTP_204_NO_CONTENT, safe=False)
        else:
            raise Exception('Order Cancellation failed for Order = ', order_id)

    def post(self, request):
        data = JSONParser().parse(request)
        order_id = data.get('metadata').get('order_id')
        amount = Decimal(data.get('amount')) * 100  # convert to cents
        cents = Decimal('0')
        amount = amount.quantize(cents)
        print('amount', amount)
        # view is not fat but payload is fat...sorry payment view
        intent = stripe.PaymentIntent.create(
            idempotency_key=util.get_idempotency_key(16),  # to avoid collisions.
            amount=amount,  # convert to cents
            currency=data.get('currency'),
            confirm=True,  # confirming the PaymentIntent
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
                "OrderId": order_id,
                "Phone": data.get('metadata').get('phone'),
                "CustomerId": data.get('metadata').get('customer_id'),
                "StoreId": data.get('metadata').get('store_id')
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


class OrderDetailView(APIView):

    def post(self, request):
        data = request.data
        serializer = OrderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

        items = data.get('items')

        for item in items:
            print(data)
            product = Product.objects.get(id=item.get('product_id'))
            order = Order.objects.get(id=item.get('order_id'))
            cents = Decimal('.01')
            line_total = product.price * Decimal(item.get('quantity'))
            line_total = line_total.quantize(cents, decimal.ROUND_HALF_UP)
            OrderItem.objects.create(product_id=product.id, order_id=order.id, extra=item.get('extra'),
                                     line_total=line_total,
                                     quantity=item.get('quantity'), canceled=item.get('canceled'))

        return JsonResponse(serializer.data, safe=False)


# Error Pages
def bad_request(request, exception):
    return JsonResponse({
        "msg": "bad request"
    }, status=status.HTTP_400_BAD_REQUEST)


def permission_denied(request, exception):
    return JsonResponse({
        "msg": "permission denied"
    }, status=status.HTTP_401_UNAUTHORIZED)


def not_found(request, exception):
    return JsonResponse({
        "msg": "resource not found"
    }, status=status.HTTP_404_NOT_FOUND)


def server_error(request):
    return JsonResponse({
        "msg": "internal server error"
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


####  India Operation Payment Views ####

class IndiaPaymentView(APIView):
    def post(self, request):
        data = JSONParser().parse(request)
        order_id = str(data.get('metadata').get('order_id'))
        amount = Decimal(data.get('amount')) * 100  # convert to cents
        paise = Decimal('0')
        amount = amount.quantize(paise)
        print('amount', amount)
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        intent = razorpay_client.order.create({
            "amount": int(amount),  # convert to cents
            "currency": data.get('currency'),
            "receipt": order_id,
            "payment_capture": 1
        }
        )
        print('Razor Pay success with order id ', intent.get('id'))
        if OrderPayment().record_payment(data, intent):
            return JsonResponse(intent)
        else:
            raise Exception('Order Payment failed for Order = ' + order_id)

    def post(self, request, razor_order_id):
        data = JSONParser().parse(request)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        order_payment = OrderPayment.objects.filter(correlation_id=razor_order_id).first()
        order_payment.transaction_id = razorpay_payment_id
        order_payment.signature = razorpay_signature
        order_payment.status = "payment_intent.succeeded"
        order_payment.save()

        recipient_email = Email()
        recipient_email.subject = "Order Confirmation for Grocery 60"
        recipient_email.email = data.get('receipt_email')
        recipient_email.order_id = order_payment.order_id
        recipient_email.set_order(order_payment.order_id)
        order_payment = OrderPayment()
        order_payment.send_success_email(recipient_email)
        return JsonResponse(data)
