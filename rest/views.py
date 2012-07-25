from functools import update_wrapper

from django.views.generic import View
from django.http import QueryDict
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from . mixins import ResourceMixin


class View(ResourceMixin, View):
    pass
