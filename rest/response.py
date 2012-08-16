import collections
import mimetypes

import mimeparse

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core import serializers
from django.db.models.query import QuerySet

from .utils.decorators import wrap_object

try:
    import simplejson as json
except ImportError:
    import json


def serialize_json(content):
    if isinstance(content, QuerySet):
        json_serializer = serializers.get_serializer('json')()
        serialized_content = json_serializer.serialize(content, ensure_ascii=False)
    else:
        json_encoder = serializers.json.DjangoJSONEncoder
        serialized_content = json.dumps(content, cls=json_encoder, ensure_ascii=False)
    return serialized_content

DEFAULT_MIMETYPE = 'application/json'
SUPPORTED_MIMETYPES = {
    'application/json': serialize_json
}


class RESTfulResponse(object):
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
        self.supported_mimetypes = SUPPORTED_MIMETYPES.copy()
        if mimetype_mapping:
            self.supported_mimetypes.update(mimetype_mapping)

    def __call__(self, view_obj):
        def decorator(view_func):
            def wrapper(request, *args, **kwargs):
                results = view_func(request, *args, **kwargs)

                # Get the status code, if one was provided
                if isinstance(results, collections.Sequence) and len(results) == 2:
                    try:
                        data, status_code = results[0], int(results[1])
                    except Exception:
                        data, status_code = results, 200
                else:
                    data, status_code = results, 200

                # TODO: What about a view that returns a normal Django
                #       HttpResponse object? Should we allow this to error
                #       out when one is encountered? Should we just allow it
                #       to propogate through (i.e., kind of an override)? Or,
                #       should we fectch the content from it and pass that to
                #       render_to_response method?
                response = self.render_to_response(request, data, status_code)
                return response
            return wrapper
        return wrap_object(view_obj, decorator)

    def render_to_response(self, request, data=None, status=200):
        mimetype = mimeparse.best_match(self.supported_mimetypes.keys(), request.META['HTTP_ACCEPT'])
        mimetype = mimetypes.guess_type(request.path_info.rstrip('/'))[0] or mimetype
        content_type = '%s; charset=%s' % (mimetype, settings.DEFAULT_CHARSET)

        templ_or_func = self.supported_mimetypes.get(mimetype)

        # If a template or function isn't found, return a 415 (unsupportted media type) response
        if not templ_or_func:
            return HttpResponse(status=415)

        if isinstance(templ_or_func, str):
            def serialize(data):
                data = data or {}
                response = render_to_response(templ_or_func, data)
                response['Content-Type'] = content_type
                response.status_code = status
                return response
        else:
            def serialize(data):
                if data:
                    response = HttpResponse(templ_or_func(data), content_type=content_type, status=status)
                else:
                    response = HttpResponse(content_type=content_type, status=status)
                return response

        return serialize(data)
