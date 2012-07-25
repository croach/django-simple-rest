from datetime import datetime

from django.views.generic import View as DjangoView
from django.http import QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.sessions.backends.db import SessionStore

# TODO: Remove the dependency on Site
from plum.console.models import Site

from .auth.signature import calculate_signature


class View(DjangoView):

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # TODO: Move to a wrapper method, decorator, something

        if request.method.lower() == 'put':
            request.method = 'POST'
            request._load_post_and_files()
            request.method = 'PUT'
            request.PUT = request.POST

        method_in_GET = request.GET.get('_method', '').lower()
        method_in_POST = request.POST.get('_method', '').lower()

        #Ok, now let's remove that method.
        if request.GET and method_in_GET:
            GET = request.GET.copy()
            request.method = GET.pop('_method')[0]
            request.GET = GET
        elif request.POST and method_in_POST:
            POST = request.POST.copy()
            request.method = POST.pop('_method')[0]
            request.POST = POST

        if (method_in_GET or method_in_POST) == 'put':
            #Manually switch POST data to PUT
            request.PUT = POST
            request.POST = QueryDict({})

        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        self.request = request
        self.args = args
        self.kwargs = kwargs

        # Handle request authentication
        if getattr(handler, 'auth_required', False):
            if request.GET.get('sig', False):
                if not self._validate_signature(request, kwargs.get('domain', None)):
                    return HttpResponseForbidden()
            else:
                handler = login_required(handler)
        elif getattr(handler, 'login_required', False):
            handler = login_required(handler)
        elif getattr(handler, 'admin_required', False):
            handler = user_passes_test(lambda u: u.is_superuser)(handler)
        elif getattr(handler, 'signature_required', False):
            if not self._validate_signature(request, kwargs.get('domain', None)):
                return HttpResponseForbidden()

        return handler(request, *args, **kwargs)


    def _validate_signature(self, request, domain):
        """
        Validates the signature associated with the given request.
        """

        # Extract the request parameters according to the HTTP method
        data = request.GET.copy()
        if request.method.lower() == 'post':
            data.update(request.POST.copy())
        elif request.method.lower() == 'put':
            data.update(request.PUT.copy())

        # TODO: Figure out another [good] way to get the secret key.
        #       The problem is that this app must now know something
        #       about the model classes that we've created, so this
        #       framework is currently coupled to our bacon app which
        #       not a very good design.
        # Get the secret key for the given domain
        try:
            site = Site.objects.get(domain=domain)
            secret_key = site.account.secret_key
        except Site.DoesNotExist:
            return False
        except Site.MultipleObjectsReturned:
            return False
        except Exception:
            return False

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
