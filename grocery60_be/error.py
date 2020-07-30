import json
import logging
from django.http import JsonResponse
import traceback
from grocery60_be import settings
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, NotFound, MethodNotAllowed, AuthenticationFailed
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
ERRORS_401 = (AuthenticationError, NotAuthenticated, AuthenticationFailed)
ERRORS_404 = (ObjectNotFound, ResourceNotExist, NotFound, ObjectDoesNotExist, Http404, HttpResponseNotFound)



def grocery60_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    error_msg = None
    if response:
        print(' Error Type ', type(exc), ' ', str(exc), ' Response Status', response.status_code)
    else:
        print(' Error Details ', type(exc), ' ', str(exc))
    # set status_code by category of the exception you caught
    if isinstance(exc, ERRORS_400):
        print(' Error Status  400')
        if str(exc).find('Unable to log in') > -1:
            error_msg = 'You do not have permission to perform this action'
            status_code = 401
        else:
            error_msg = 'Bad request for resource'
            status_code = 400
    elif isinstance(exc, ERRORS_401):
        error_msg = 'You do not have permission to perform this action'
        print(' Error Status  401')
        status_code = 401
    elif isinstance(exc, ERRORS_404):
        print(' Error Status  404')
        error_msg = 'Resource does not exists at requested url'
        status_code = 404
    else:
        # if the exception not belone to any one you expected,
        # or you just want the response to be 500
        error_msg = 'Service temporarily unavailable, try again later'
        status_code = 500
        # you can do something like write an error log or send report mail here
        logging.error(exc)
    response_dict = {
        'status': 'error',
        # the format of error message determined by you base exception class
        'msg': error_msg,
        'message': str(exc)
    }
    if settings.DEBUG or True:
        # you can even get the traceback infomation when you are in debug mode
        # response_dict['traceback'] = traceback.format_exc()
        track = traceback.format_exc()
        print('-------track start--------')
        print(track)
        print('-------track end--------')

    return JsonResponse(response_dict, status=status_code)
