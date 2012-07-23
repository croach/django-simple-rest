from functools import update_wrapper

from django.views.generic import View
from django.http import QueryDict

from plum.rest.mixins import ResourceMixin

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class View(ResourceMixin, View):
    pass
