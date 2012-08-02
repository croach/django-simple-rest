from functools import wraps
import mimetypes

import mimeparse

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core import serializers
from django.utils.decorators import method_decorator, available_attrs
from django.db.models.query import QuerySet

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
    def __init__(self, mimetype_mapping=None):
        self.supported_mimetypes = SUPPORTED_MIMETYPES.copy()
        if mimetype_mapping:
            self.supported_mimetypes.update(mimetype_mapping)


    def __call__(self, view_obj):
        def wrapper(resource, request, *args, **kwargs):
            context_dict = view_obj(resource, request, *args, **kwargs)
            response = self._create_response(request, context_dict)
            return response

        return wrapper

    def _create_response(self, request, context_dict):
        mimetype = mimeparse.best_match(self.supported_mimetypes.keys(), request.META['HTTP_ACCEPT'])
        # mimetype = mimetypes.guess_type(request.path_info)[0] || mimetype
        content_type = '%s; charset=%s' % (mimetype, settings.DEFAULT_CHARSET)

        templ_or_func = self.supported_mimetypes.get(mimetype)
        if not templ_or_func:
            templ_or_func = self.supported_mimetypes[DEFAULT_MIMETYPE]

        if isinstance(templ_or_func, str):
            def serializer(context_dict):
                response = render_to_response(templ_or_func, context_dict)
                response['Content-Type'] = content_type
                return response
        else:
            def serializer(context_dict):
                serializer = self.supported_mimetypes[mimetype]
                response = HttpResponse(serializer(context_dict), content_type=content_type)
                return response

        return serializer(context_dict)
