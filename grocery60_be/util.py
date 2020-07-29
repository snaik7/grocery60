import string
import random


def get_idempotency_key(length):
    return generate_random_string(length)


def generate_password(length):
    return generate_random_string(length)


def generate_token(length):
    return generate_random_numbers(length)


def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def generate_random_numbers(length):
    numbers = string.digits
    return ''.join(random.choice(numbers) for i in range(length))
