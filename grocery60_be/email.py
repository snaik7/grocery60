import json

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from grocery60_be import settings
from google.cloud import pubsub_v1

def send_email(email, template):
    print('*********************** email send template started ***********************')
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
        'host': settings.ALLOWED_HOSTS[2],
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

def send_email(email):
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(settings.PROJECT, 'email')

    data = vars(email)
    print('data', data )

    # Data must be a bytestring
    # using encode() + dumps() to convert to bytes
    data_bytes = json.dumps(data).encode('utf-8')
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, data=data_bytes)
    print(future.result())

    print("Published messages.")
