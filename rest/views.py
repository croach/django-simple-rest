from django.views.generic import View as DjangoView
from django.http import QueryDict
from django.views.decorators.csrf import csrf_exempt


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

        return handler(request, *args, **kwargs)
