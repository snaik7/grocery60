from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email(email, template):
    print('*********************** email send template sratrted ***********************')
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
        'email': email.email,
    }

    # render email text
    email_message = render_to_string(template, context)

    msg = EmailMultiAlternatives(
        # title:
        "Order Confirmation for {title}".format(title="Grocery60"),
        # message:
        email_message,
        # from:
        "admin@grocery60.com",
        # to:
        [email.email]
    )
    msg.attach_alternative(email_message, "text/html")
    msg.send()