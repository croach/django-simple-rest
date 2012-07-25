import inspect
from datetime import datetime
from functools import wraps

from django.utils.decorators import method_decorator, available_attrs

from .signature import calculate_signature
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


def login_required(obj):  # TODO: Add the redirect_field_name and login_url fields
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


def request_passes_test(test_func):
    """
    Decorator for resources that checks that the request passes the given test.
    If the request fails the test a 401 (Unauthorized) response is returned,
    otherwise the view is executed normally. The test should be a callable that
    takes an HttpRequest object and any number of positional and keyword
    arguments as defined by the urlconf entry for the decorated resource.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request, *args, **kwargs):
                return view_func(request, *args, **kwargs)
            raise HttpError(status=401)
        return _wrapped_view
    return decorator


def wrap_object(obj, decorator):
    """
    Decorates the given object with the decorator function.

    If obj is a method, the method is decorated with the decorator function
    and returned. If obj is a class (i.e., a class based view), the methods
    in the class corresponding to HTTP methods will be decorated and the
    resultant class object will be returned.
    """
    actual_decorator = method_decorator(decorator)

    if inspect.isfunction(obj):
        wrapped_obj = actual_decorator(obj)
    elif inspect.isclass(obj):
        for method_name in obj.http_method_names:
            if hasattr(obj, method_name):
                method = getattr(obj, method_name)
                setattr(obj, method_name, actual_decorator(method))
        wrapped_obj = obj
    else:
        raise TypeError("received an object of type '{0}' expected 'function' or 'classobj'.".format(type(obj)))

    return wrapped_obj


def validate_signature(request, secret_key):
    """
    Validates the signature associated with the given request.
    """

    # Extract the request parameters according to the HTTP method
    data = request.GET.copy()
    if request.method.lower() == 'post':
        data.update(request.POST.copy())
    elif request.method.lower() == 'put':
        data.update(request.PUT.copy())

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
    delta = datetime.utcnow() - datetime.utcfromtimestamp(timestamp)
    if delta.seconds > 5 * 60:  # If the signature is older than 5 minutes, it's invalid
        return False

    # Make sure the signature is valid
    return sig == calculate_signature(secret_key, data, timestamp)
