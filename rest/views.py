from django.views.generic import View as DjangoView
from django.http import QueryDict
from django.views.decorators.csrf import csrf_exempt


class View(DjangoView):

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # If the HTTP method is PUT, add PUT attribute to the request,
        # and point it at the POST QueryDict
        import ipdb; ipdb.set_trace()
        if request.method.lower() == 'put':
            request.method = 'POST'
            request._load_post_and_files()
            request.method = 'PUT'
            request.PUT = request.POST

        # Check for an overriding method in the GET or POST data,
        # and set the HTTP method on the request appropriately
        if request.GET and request.GET.get('_method', None):
            GET = request.GET.copy()
            request.method = GET.pop('_method')[0].upper()
            request.GET = GET
            request.PUT = request.GET
        elif request.POST and request.POST.get('_method', None):
            POST = request.POST.copy()
            request.method = POST.pop('_method')[0].upper()
            request.POST = POST
            request.PUT = request.POST

        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        # Have to set request on the View object to make http_method_not_allowed happy
        self.request = request

        return handler(request, *args, **kwargs)
