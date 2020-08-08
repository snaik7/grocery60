import datetime
import time
from decimal import Decimal
from datetime import datetime, timedelta

import stripe
from django.db.models import Count

from grocery60_be.models import OrderPayment
from grocery60_be import settings

def notification_listener(event):
    if event.exception:
        print(event.exception)
        print('The job crashed :(')
    else:
        print('The job worked :)')


def payout_store():
    print('running schedule job at ', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

    '''
    topup = stripe.Topup.create(
        amount=2000,
        currency='usd',
        description='Top-up for week of May 31',
        statement_descriptor='Weekly top-up',
    )
    '''
    '''
    fetcher = lazy_bulk_fetch(10,
                              OrderPayment.objects.filter(payout_status='READY_TO_PAY').order_by('created_at').count(),
                              lambda: OrderPayment.objects.select_related('store').filter(
                                  payout_status='READY_TO_PAY').order_by('created_at'))
    '''
    time_threshold = datetime.now() - timedelta(days=settings.PAYMENT_DELAY)
    print('Retrieving before ', time_threshold)
    fetcher = OrderPayment.objects.select_related('store').filter(
                                  payout_status='READY_TO_PAY', updated_at__lt=time_threshold).order_by('created_at')[:settings.PAYMENT_COUNT]
    for order_payment in fetcher:
        print("Batch Started", order_payment.annotate(Count('id')))
        for payment in order_payment:
            print("Record Processing")
            amount = Decimal(payment.amount) * 100  # convert to cents
            cents = Decimal('0')
            amount = amount.quantize(cents)
            print('payment', payment.id, ' amount', amount, 'store account', payment.store.payment_account)
            transfer = None
            try:
                if payment.store.payment_account:
                    print('transfer')
                    transfer = stripe.Transfer.create(
                        amount=amount,
                        currency="usd",
                        destination="acct_1H92XPFQ5Tn2vT0x"
                    )
                    payment.status = 'COMPLETED'
                    payment.payout_status = 'COMPLETED'
                    payment.payout_id = transfer.get('id')
                else:
                    msg = "Store payment method not set"
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                if transfer:
                    print('transfer' + transfer)
                payment.payout_status = 'FAILED'
                msg = e.error.type + '  ' + str(e.error.code) + '  ' + e.error.message
                pass
            payment.payout_message = msg
            payment.save()


def lazy_bulk_fetch(max_obj, max_count, fetch_func, start=0):
    counter = start
    while counter < max_count:
        yield fetch_func()[counter:counter + max_obj]
        counter += max_obj
