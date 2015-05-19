from datetime import datetime

from django.http import HttpResponse

from .signature import calculate_signature
from ..utils.decorators import wrap_object
from ..exceptions import HttpError


def auth_required(secret_key_func):
    """
    Requires that the user be authenticated either by a signature or by
    being actively logged in.
    """
    def actual_decorator(obj):

        def test_func(request, *args, **kwargs):
            secret_key = secret_key_func(request, *args, **kwargs)
            return validate_signature(request, secret_key) or request.user.is_authenticated()

        decorator = request_passes_test(test_func)
        return wrap_object(obj, decorator)

    return actual_decorator


def login_required(obj):
    """
    Requires that the user be logged in order to gain access to the resource
    at the specified the URI.
    """
    decorator = request_passes_test(lambda r, *args, **kwargs: r.user.is_authenticated())
    return wrap_object(obj, decorator)


def admin_required(obj):
    """
    Requires that the user be logged AND be set as a superuser
    """
    decorator = request_passes_test(lambda r, *args, **kwargs: r.user.is_superuser)
    return wrap_object(obj, decorator)


def signature_required(secret_key_func):
    """
    Requires that the request contain a valid signature to gain access
    to a specified resource.
    """
    def actual_decorator(obj):

        def test_func(request, *args, **kwargs):
            secret_key = secret_key_func(request, *args, **kwargs)
            return validate_signature(request, secret_key)

        decorator = request_passes_test(test_func)
        return wrap_object(obj, decorator)

    return actual_decorator


def request_passes_test(test_func, message=None, status=401):
    """
    Decorator for resources that checks that the request passes the given test.
    If the request fails the test a 401 (Unauthorized) response is returned,
    otherwise the view is executed normally. The test should be a callable that
    takes an HttpRequest object and any number of positional and keyword
    arguments as defined by the urlconf entry for the decorated resource.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not test_func(request, *args, **kwargs):
                raise HttpError(message=message, status=status)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def validate_signature(request, secret_key):
    """
    Validates the signature associated with the given request.
    """

    # Extract the request parameters according to the HTTP method
    data = request.GET.copy()
    if request.method != 'GET':
        message_body = getattr(request, request.method, {})
        data.update(message_body)

    # Make sure the request contains a signature
    if data.get('sig', False):
        sig = data['sig']
        del data['sig']
    else:
        return False

    # Make sure the request contains a timestamp
    if data.get('t', False):
        timestamp = int(data.get('t', False))
        del data['t']
    else:
        return False

    # Make sure the signature has not expired
    local_time = datetime.utcnow()
    remote_time = datetime.utcfromtimestamp(timestamp)
    
    
    # this stops a bug if the client clock is ever a little ahead of 
    # the server clock.  Makes the window of acceptable time current +/- 5 mins
    if local_time > remote_time:
        delta = local_time - remote_time
    else:   
        delta = remote_time - local_time
    
    if delta.seconds > 5 * 60:  # If the signature is older than 5 minutes, it's invalid
        return False

    # Make sure the signature is valid
    return sig == calculate_signature(secret_key, data, timestamp)
