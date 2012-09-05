from django.http import HttpResponse

from .response import RESTfulResponse


class HttpError(Exception):
    def __init__(self, message=None, status=500):
        super(HttpError, self).__init__(message)
        self.status = status

    def __repr__(self):
        return 'HttpError(%r, %r)' % (self.status, self.message)


class ExceptionMiddleware(object):
    def process_exception(self, request, exception):
        """
        Returns the proper HttpRespone if an HttpError was thrown
        """
        response = None
        if isinstance(exception, HttpError):
            if exception.message:
                context_dict = {'message': exception.message}
                response = RESTfulResponse().render_to_response(request, context_dict, exception.status)
            else:
                response = RESTfulResponse().render_to_response(request, status=exception.status)
        return response
