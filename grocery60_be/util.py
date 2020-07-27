import string
import random


def get_idempotency_key(length):
    letters = string.ascii_lowercase
    idempotency_key = ''.join(random.choice(letters) for i in range(length))
    return idempotency_key

def generate_password(length):
    letters = string.ascii_lowercase
    password = ''.join(random.choice(letters) for i in range(length))
    return password