from decimal import Decimal
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.template import Template, Context

import logging
logger = logging.getLogger(__name__)

try:
    from pygments import highlight
    from pygments.lexers import JSONLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_INSTALLED = True
except Exception, e:
    logging.info("Install pygments for syntax highlighting")
    PYGMENTS_INSTALLED = False

try:
    import simplejson as json
except ImportError:
    logging.info('Install simplejson for better performance')
    import json


class DecimalEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return DjangoJSONEncoder.default(self, obj)


def to_json(content, indent=None):
    """
    Serializes a python object as JSON

    This method uses the DJangoJSONEncoder to to ensure that python objects
    such as Decimal objects are properly serialized. It can also serialize
    Django QuerySet objects.
    """
    if isinstance(content, QuerySet):
        json_serializer = serializers.get_serializer('json')()
        serialized_content = json_serializer.serialize(content, ensure_ascii=False, indent=indent)
    else:
        try:
            serialized_content = json.dumps(content, cls=DecimalEncoder, ensure_ascii=False, indent=indent)
        except TypeError:
            # Fix for Django 1.5
            serialized_content = json.dumps(content, ensure_ascii=False, indent=indent)
    return serialized_content


def to_html(data):
    """
    Serializes a python object as HTML

    This method uses the to_json method to turn the given data object into
    formatted JSON that is displayed in an HTML page. If pygments in installed,
    syntax highlighting will also be applied to the JSON.
    """
    base_html_template = Template('''
        <html>
            <head>
                {% if style %}
                <style type="text/css">
                    {{ style }}
                </style>
                {% endif %}
            </head>
            <body>
                {% if style %}
                    {{ body|safe }}
                {% else %}
                    <pre></code>{{ body }}</code></pre>
                {% endif %}
            </body>
        </html>
        ''')

    code = to_json(data, indent=4)
    if PYGMENTS_INSTALLED:
        c = Context({
            'body': highlight(code, JSONLexer(), HtmlFormatter()),
            'style': HtmlFormatter().get_style_defs('.highlight')
        })
        html = base_html_template.render(c)
    else:
        c = Context({'body': code})
        html = base_html_template.render(c)
    return html

def to_text(data):
    """
    Serializes a python object as plain text

    If the data can be serialized as JSON, this method will use the to_json
    method to format the data, otherwise the data is returned as is.
    """
    try:
        serialized_content = to_json(data, indent=4)
    except Exception, e:
        serialized_content = data
    return serialized_content



