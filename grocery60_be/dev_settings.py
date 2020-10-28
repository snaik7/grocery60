"""
Django settings for grocery60_be project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import environ
import stripe
import logging
# Imports the Cloud Logging client library
import google.cloud.logging  # Don't conflict with standard logging
from google.cloud.logging.handlers import CloudLoggingHandler, setup_logging

# Import settings with django-environ
env = environ.Env()
build = 'dev'

# Import settings from Secret Manager
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_file = os.path.join(BASE_DIR, ".env")

if not os.path.isfile('.env'):
    import google.auth
    from google.cloud import secretmanager_v1beta1 as sm

    _, project = google.auth.default()

    if project:
        client = sm.SecretManagerServiceClient()
        path = client.secret_version_path(project, "django_settings", "latest")
        payload = client.access_secret_version(path).payload.data.decode("UTF-8")

        with open(env_file, "w") as f:
            f.write(payload)

env = environ.Env()
env.read_env(env_file)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = '6#k#c$w9-v35=f-prrr)s25t0q75px)iu4m6c&((&_w42fa!%4'

SECRET_KEY = env("SECRET_KEY")

# SECRET_KEY = '6#k#c$w9-v35=f-prrr)s25t0q75px)iu4m6c&((&_w42fa!%4'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*','grocery60-be-xtpocjmkpa-uw.a.run.app','https://grocery60-be-prod-xtpocjmkpa-uw.a.run.app']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'grocery60_be',  # for a later data migration
    'storages',  # for django-storages
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'corsheaders',
    # libraries
    'graphene_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'grocery60_be.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'grocery60_be.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'grocery60_be.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# Understand limit of gcp connecions -  https://cloud.google.com/sql/docs/postgres/quotas
# default max connections = 25

# Use django-environ to define the connection string
DATABASES = {"default": env.db()}

AUTH_USER_MODEL = 'grocery60_be.User'

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator", },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator", },
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator", },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

# Define static storage via django-storages[google]
GS_BUCKET_NAME = env("GS_BUCKET_NAME", None)

DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_DEFAULT_ACL = "publicRead"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'EXCEPTION_HANDLER': 'grocery60_be.error.grocery60_exception_handler',
}

# Set your secret key. Remember to switch to your live secret key in production!
# See your keys here: https://dashboard.stripe.com/account/apikeys
stripe.api_key = env("STRIPE_PUBKEY")
stripe.api_version = os.getenv('STRIPE_APIKEY', '2020-03-02')
# set on each request
stripe_account = "acct_1HSZgsKNK8C6rbwM"

#PROJECT = 'named-enigma-277405'
PROJECT = 'grocery60-project'

# Instantiates a client
client = google.cloud.logging.Client()

# Retrieves a Cloud Logging handler based on the environment
# you're running in and integrates the handler with the
# Python logging module. By default this captures all logs
# at INFO level and higher

handler = CloudLoggingHandler(client)
logging.getLogger().setLevel(logging.INFO)  # defaults to WARN
setup_logging(handler)

CORS_ORIGIN_ALLOW_ALL = True  # If this is used then `CORS_ORIGIN_WHITELIST` will not have any effect
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = [
    'http://localhost:3030',
]  # If this is used, then not need to use `CORS_ORIGIN_ALLOW_ALL = True`
CORS_ORIGIN_REGEX_WHITELIST = [
    'http://localhost:3030',
]
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'no-reply@grocery60.online'
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

GRAPHENE = {
    'SCHEMA': 'grocery60_be.schema.schema'
}

GRAPHQL_TOKEN = env('GRAPHQL_TOKEN')
SERVICE_FEE = 7
DISCOUNT = 0
DELIVERY_PER_MILE = 0.5
DELIVERY_FREE_MILES = 10
PAYMENT_COUNT = 10
PAYMENT_DELAY = 15
PAYMENT_SCHEDULER_DELAY = 360  # in mins

RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET")

#set for product search
REGION = 'us-west1'
API_KEY = env("API_KEY")
SEARCH_ENGINE_ID = 'cc67409fec6045edd'

