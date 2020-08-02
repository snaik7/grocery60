import asyncio

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from grocery60_be import settings


def send_email(email, template):
    print('*********************** email send template started ***********************')
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    context = {
        'order_id': email.order_id,
        'first_name': email.first_name,
        'email': email.email,
        'order_items_list': email.order_items_list,
        'subtotal': email.subtotal,
        'tax': email.tax,
        'discount': email.discount,
        'tip': email.tip,
        'service_fee': email.service_fee,
        'shipping_fee': email.shipping_fee,
        'total': email.total,
        'username': email.username,
        'password': email.password,
        'token': email.token,
        'host': settings.ALLOWED_HOSTS[1],
        # 'host': 'http://localhost:8000',
    }

    # render email text
    email_message = render_to_string(template, context)

    msg = EmailMultiAlternatives(
        # title:
        " {subject}".format(subject=email.subject),
        # message:
        email_message,
        # from:
        "no-reply@grocery60.online",
        # to:
        [email.email]
    )
    msg.attach_alternative(email_message, "text/html")
    msg.send()
    print('email sent')
