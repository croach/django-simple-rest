import inspect
from functools import update_wrapper

from django.utils.decorators import method_decorator, available_attrs


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
        update_wrapper(wrapped_obj, obj, assigned=available_attrs(obj))
    elif inspect.isclass(obj):
        for method_name in obj.http_method_names:
            if hasattr(obj, method_name):
                method = getattr(obj, method_name)
                wrapped_method = actual_decorator(method)
                update_wrapper(wrapped_method, method, assigned=available_attrs(method))
                setattr(obj, method_name, wrapped_method)
        wrapped_obj = obj
    else:
        raise TypeError("received an object of type '{0}' expected 'function' or 'classobj'.".format(type(obj)))

    return wrapped_obj
