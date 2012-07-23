import inspect
from functools import WRAPPER_ASSIGNMENTS, update_wrapper

def auth_required(wrapped_obj):
    """
    Requires that the user be authenticated either by a signature or by 
    being actively logged in.
    """
    return _auth_wrapper(wrapped_obj)

def login_required(wrapped_obj): # TODO: Add the redirect_field_name and login_url fields
    """
    Requires that the user be logged in order to gain access to the resource
    at the specified the URI.
    """
    return _auth_wrapper(wrapped_obj, 'login')

def admin_required(wrapped_obj): 
    """
    Requires that the user be logged AND be set as a superuser
    """
    return _auth_wrapper(wrapped_obj, 'admin')

def signature_required(wrapped_obj):
    """
    Requires that the request contain a valid signature to gain access
    to a specified resource.
    """
    return _auth_wrapper(wrapped_obj, 'signature')


def _auth_wrapper(wrapped_obj, auth_type=None): # TODO: Add the redirect_field_name and login_url fields
    """
    Returns a function (or class object) that requires that the user be 
    authenticated according to the auth_type parameter to gain access
    to the function (or methods) within. The default authentication type 
    is a cascading auth. If a signature is found, it will be used to 
    authenticate the user's request, otherwise, the request will be allowed
    if a valid session exists.
    """
    if inspect.isfunction(wrapped_obj):            
        decorator = _auth_required_function_decorator(auth_type)
    elif inspect.isclass(wrapped_obj):
        decorator = _auth_required_class_decorator(auth_type)
    else:
        raise TypeError("received an object of type '{0}' expected 'function' or 'classobj'.".format(type(wrapped_obj)))
    return decorator(wrapped_obj)
        
def _auth_required_class_decorator(auth_type=None):
    func_decorator = _auth_required_function_decorator(auth_type)
    def decorator(cls):
        for method in cls.http_method_names:
            if hasattr(cls, method):
                func = getattr(cls, method)
                setattr(cls, method, func_decorator(func))
        return cls
    return decorator
    
def _auth_required_function_decorator(auth_type=None):
    # Decorators really should be side effect free and not
    # manipulate the function they wrap, so we create a 
    # new function and add the login_required flag to it.
    def decorator(func):
        def wrapped_view(*args, **kwargs):
            return func(*args, **kwargs)
            
        # Set the authentication type flag on the wrapped_view
        if not auth_type:
            wrapped_view.auth_required = True
        elif auth_type == 'login':
            wrapped_view.login_required = True
        elif auth_type == 'signature':
            wrapped_view.signature_required = True
        elif auth_type == 'admin':
            wrapped_view.admin_required = True
        else:
            raise ValueError("Invalid auth_type. Expected 'login' or 'signature' found {0}.".format(auth_type))
            
        # Update the wrapped_view to have the same signature, docs, etc as the view it wraps
        assigned_attrs = set(WRAPPER_ASSIGNMENTS) & set(dir(wrapped_view))
        return update_wrapper(wrapped_view, func, assigned=assigned_attrs)
    return decorator
