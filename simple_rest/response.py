import collections
import mimetypes

import mimeparse

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse

from .utils.decorators import wrap_object
from .exceptions import HttpError
from .utils.serializers import to_json, to_html, to_text


DEFAULT_MIMETYPES = {
    'application/json': to_json,
    'text/html': to_html,
    'text/plain': to_text
}


class RESTfulResponse(collections.MutableMapping, collections.Callable):
    """
    Can be used as a decorator or an instance to properly formatted content

    This class provides content negotiation for RESTful requests. The content-
    type of a response is determined by the ACCEPT header of the reqeust or by
    an overriding file extension in the URL (e.g., path/to/some/resource.xml)
    will return the response formatted as XML.

    This class creates an instance that can be used directly to transform a
    python dict into a properly formatted response via the render_to_response
    method or it can be used as a decorator for class-based views or for an
    individual method within a class-based view. If a requested mimetype is
    not found amongst the supported mimetypes, the content-type of the response
    will default to 'application/json'.

    This class is inspired by an excellent blog post from James Bennett. See
    http://www.b-list.org/weblog/2008/nov/29/multiresponse/ for more
    information.
    """
    def __init__(self, mimetype_mapping=None):
        self._mimetypes = {}
        if mimetype_mapping:
            self._mimetypes.update(mimetype_mapping)

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        for key in self.keys():
            yield key

    def __getitem__(self, mimetype):
        if mimetype in self._mimetypes:
            return self._mimetypes[mimetype]
        else:
            return DEFAULT_MIMETYPES[mimetype]

    def __setitem__(self, mimetype, func_or_templ):
        self._mimetypes[mimetype] = func_or_templ

    def __delitem__(self, mimetype):
        del self._mimetypes[mimetype]

    def keys(self):
        return list(set(self._mimetypes.keys()) | set(DEFAULT_MIMETYPES.keys()))

    def __call__(self, view_obj):
        def decorator(view_func):
            def wrapper(request, *args, **kwargs):
                try:
                    results = view_func(request, *args, **kwargs)
                except HttpError, e:
                    results = (
                        e.message and {'error': e.message} or None,
                        e.status
                    )

                # TODO: What should be done about a resource that returns a normal
                #       Django HttpResponse? Right now, if an HttpResponse is
                #       returned, it is allowed to propogate. In other words, it
                #       acts just as it would if content negotiation wasn't being
                #       used. Another option would be to extract the content and
                #       status code from the HttpResponse object and pass those
                #       into the render_to_response method.
                if isinstance(results, HttpResponse):
                    return results

                # Get the status code, if one was provided
                if isinstance(results, collections.Sequence) and len(results) == 2:
                    try:
                        data, status_code = results[0], int(results[1])
                    except Exception:
                        data, status_code = results, 200
                else:
                    data, status_code = results, 200

                response = self.render_to_response(request, data, status_code, kwargs.get('_format', None))
                return response
            return wrapper
        return wrap_object(view_obj, decorator)

    def render_to_response(self, request, data=None, status=200, format=None):
        format = request.REQUEST.get('_format', None) or format
        mimetype = mimeparse.best_match(self.keys(), request.META.get('HTTP_ACCEPT', ''))
        mimetype = mimetypes.guess_type('placeholder_filename.%s' % format)[0] or mimetype
        content_type = '%s; charset=%s' % (mimetype, settings.DEFAULT_CHARSET)

        templ_or_func = self.get(mimetype)

        # If a template or function isn't found, return a 415 (unsupportted media type) response
        if not templ_or_func:
            return HttpResponse(status=415)

        if data is None:
            response = HttpResponse()
        elif isinstance(templ_or_func, str):
            response = render_to_response(templ_or_func, {'context': data})
        else:
            response = HttpResponse(templ_or_func(data))

        response['Content-Type'] = content_type
        response.status_code = status
        return response
