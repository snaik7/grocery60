import json
import logging
from django.http import JsonResponse
import traceback
from grocery60_be import settings
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, NotFound, MethodNotAllowed
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework import exceptions
from django.http.response import Http404, HttpResponseBadRequest, HttpResponseNotFound


# define Python user-defined exceptions

class ValidationError(Exception):
    """Raised when the input value is invalid"""
    pass


class AuthenticationError(Exception):
    """Raised when the authentication failed"""
    pass


class ObjectNotFound(Exception):
    """Raised when the object not found"""
    pass


class ResourceNotExist(Exception):
    """Raised when the resource not found"""
    pass


class ServiceException(Exception):
    """Raised when the service exception"""
    pass


# categorize your exceptions
ERRORS_400 = (
ValidationError, exceptions.ValidationError, RestValidationError, HttpResponseBadRequest, MethodNotAllowed)
ERRORS_401 = (AuthenticationError, NotAuthenticated)
ERRORS_404 = (ObjectNotFound, ResourceNotExist, NotFound, ObjectDoesNotExist, Http404, HttpResponseNotFound)


def grocery60_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    print(' Error Type ', type(exc), ' Response Status', response.status_code)
    print(' Error Details ', str(exc))
    # set status_code by category of the exception you caught
    if isinstance(exc, ERRORS_400):
        print(' Error Status  400')
        if str(exc).find('Unable to log in') > -1:
            status_code = 401
        else:
            status_code = 400
    elif isinstance(exc, ERRORS_401):
        print(' Error Status  401')
        status_code = 401
    elif isinstance(exc, ERRORS_404):
        print(' Error Status  404')
        status_code = 404
    else:
        # if the exception not belone to any one you expected,
        # or you just want the response to be 500
        status_code = 500
        # you can do something like write an error log or send report mail here
        logging.error(exc)
    response_dict = {
        'status': 'error',
        # the format of error message determined by you base exception class
        'msg': str(exc)
    }
    if settings.DEBUG:
        # you can even get the traceback infomation when you are in debug mode
        # response_dict['traceback'] = traceback.format_exc()
        track = traceback.format_exc()
        print('-------track start--------')
        print(track)
        print('-------track end--------')

    return JsonResponse(response_dict, status=status_code)
