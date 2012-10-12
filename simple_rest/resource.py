from django.http import HttpResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from .exceptions import HttpError


class Resource(View):

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # Technically, the HTTP spec does not preclude any HTTP request from
        # containing data in the message body, so load the data into the POST
        # dict if there is any present
        method = request.method
        request.method = 'POST'
        request._load_post_and_files()

        # Now that message body has been loaded, check for a method override
        method_override = None
        if request.GET and request.GET.get('_method', None):
            request.GET._mutable = True
            method_override = request.GET.pop('_method')[0].upper()
            request.GET._mutable = False
        elif request.POST and request.POST.get('_method', None):
            request.POST._mutable = True
            method_override = request.POST.pop('_method')[0].upper()
            request.POST._mutable = False

        # Set the HTTP method on the request according to the override first
        # if one exists, and if not, set it back to the original method used
        request.method = method_override or method

        # Add a dict to hold the message body data to the request based on the
        # HTTP method used (or the method override if one was provided)
        if request.method not in ['POST', 'GET']:
            setattr(request, request.method, request.POST)

        # Check for an HttpError when executing the view. If one was returned,
        # get the message and status code and return it, otherwise, let any
        # other type of exception bubble up or return the response if no error
        # occurred.
        try:
            response = super(Resource, self).dispatch(request, *args, **kwargs)
        except HttpError, e:
            if e.message:
                response = HttpResponse(e.message, status=e.status)
            else:
                response = HttpResponse(status=e.status)

        return response
