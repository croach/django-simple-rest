##################
Django Simple REST
##################

Django Simple REST is a very light framework that provides only the bare bones basics of what is needed to create RESTful APIs on top of Django.

############
Installation
############

1. Install using pip or easy_install: 

   - ``pip install rest`` or ``easy_install install rest``
2. Add the ExceptionMiddleware to the list of middleware classes (optional):

   - ``MIDDLEWARE_CLASSES += ['rest.exceptions.ExceptionMiddleware']``
   - This step is optional and is only needed if you want to be able to raise an HttpError from a view.
3. Add the package to the list of installed apps (optional): 
   
   - ``INSTALLED_APPS += ['rest']``
   - This step is optional and is only needed if you plan on using the supplied custom django command(s).

###########################
Why Another REST Framework?
###########################

That's a great question, and the simplest answer to it is that this really isn't a framework at all, but let me explain a bit further.

With the introduction of class-based views in version 1.3 of Django, the web framework has nearly everything it needs built in to create RESTful APIs, but just a few things are missing. This "framework" supplies those last few things.

Think of Simple REST as the code that you would have written to get class-based views working properly as a platform for RESTful API development. Looked at from that view, you start to understand what Simple REST1 is; it's a collection of code that makes it possible to create RESTful APIs with Django's class-based views, nothing more and nothing less.

If you like creating your API by hand, laboring over every last URL, then this is the framework for you. If you want something a little more full featured that handles creating large swaths of your API from Django models and things like that, let me suggest a few excellent frameworks: `Tastypie`_, `Piston`_, and `Django REST`_.

################
How do I use it?
################

There's nothing to it, it works just like you'd expect it to---assuming you're familiar with Django's `class based views`_. Let's take a look at an example::

    # ===============
    # views.py
    # ===============

    import shelve
    import json

    from django.http import HttpResponse

    from rest import Resource
    from rest.exceptions import HttpError


    class MyResource(Resource):

        def get(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            data = dict(db)
            db.close()
            return HttpResponse(json.dumps(data), content_type='application/json', status=200)

        def post(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            name = request.POST.get('name', '')
            db[name] = True
            db.sync()
            db.close()
            return HttpResponse(status=201)

        def delete(self, request, name):
            db = shelve.open('/tmp/db')
            if not db.has_key(str(name)):
                db.close()
                raise HttpError('Name does not exist', status=404)
            del(db[name])
            db.sync()
            db.close()
            return HttpResponse(status=200)

So, in the example ``views.py`` above, we've imported the ``Resource`` class, which simply inherits from Django's ``View`` class and provides the extra sauce to get all of the HTTP methods working properly. Then, we create a new class that inherits from the ``Resource`` class, and we add a function to our new class to handle each HTTP method that we want to allow. The only requirement is that the function name must match the HTTP method name, so `get` or `GET` for a GET call and so forth. Simple enough, right? So, let's see how to hook up our resource::

    # ===============
    # urls.py
    # ===============
    from django.conf.urls import patterns, include, url

    from .views import MyResource

    urlpatterns = patterns('',
        url(r'^api/resource/?$', MyResource.as_view()),
        url(r'^api/resource/(?P<name>[a-zA-Z-]+)/?$', MyResource.as_view()),
    )

The sample ``urls.py`` above shows exactly how we would go about creating the URL patterns for our example resource. Again, if you're familiar with Django class based views, there should be no surprises here.

##############
Authentication
##############

So what about authentication? Well, you could simply use the ``method_decorator`` function as the `Django docs suggest`_ to decorate each method in your resource with the appropriate authentication decorator. Assuming you want the entire resource protected you could also decorate the result of the call to ``as_view`` in the URLconf. Both of these options are completely valid and you can feel free to use them, this framework does provide another option, however.

In the ``rest.auth.decorators`` module you'll find decorators there that you can use to add authentication to your resources. Let's take a look at a few examples using our sample code from above::

    # ===============
    # views.py
    # ===============

    import shelve
    import json

    from django.http import HttpResponse

    from rest import Resource
    from rest.exceptions import HttpError
    from rest.auth.decorators import login_required, admin_required


    class MyResource(Resource):

        def get(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            data = dict(db)
            db.close()
            return HttpResponse(json.dumps(data), content_type='application/json', status=200)

        @login_required
        def post(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            name = request.POST.get('name', '')
            db[name] = True
            db.sync()
            db.close()
            return HttpResponse(status=201)

        @admin_required
        def delete(self, request, name):
            db = shelve.open('/tmp/db')
            if not db.has_key(str(name)):
                db.close()
                raise HttpError('Name does not exist', status=404)
            del(db[name])
            db.sync()
            db.close()
            return HttpResponse(status=200)

Assuming that we don't mind if anyone sees our collection of names, we can leave that one as is, but let's assume that we have strict requirements for who can add and delete names. Assuming that only registered users can add names, we add the ``login_required`` decorator to the ``post`` method. We don't mind if any our members add new names, but we don't want a name to be accidentally deleted from our database, so let's decorate that one differently with the ``admin_required`` decorator. ``admin_required`` simply makes sure that the user is logged in and is a super user before they will be granted access to the view function.

Now, this can get a bit tedious if we have lots of resources and they all tend to have the same authentication requirements. So, the authentication decorators work on both classes and methods. In the example below we're adding a superuser requirement to every method offered by the resource simply by decorating the resource class::

    # ===============
    # views.py
    # ===============

    import shelve
    import json

    from django.http import HttpResponse

    from rest import Resource
    from rest.exceptions import HttpError
    from rest.auth.decorators import admin_required


    @admin_required
    class MyResource(Resource):

        def get(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            data = dict(db)
            db.close()
            return HttpResponse(json.dumps(data), content_type='application/json', status=200)

        def post(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            name = request.POST.get('name', '')
            db[name] = True
            db.sync()
            db.close()
            return HttpResponse(status=201)

        def delete(self, request, name):
            db = shelve.open('/tmp/db')
            if not db.has_key(str(name)):
                db.close()
                raise HttpError('Name does not exist', status=404)
            del(db[name])
            db.sync()
            db.close()
            return HttpResponse(status=200)

Before we leave the topic of authentication decorators there are two more items I'd like to point out. First, another good reason for using the framework's authentication decorators whenever possible is that when authentication fails they return the correct response from a RESTful point of view. The typical Django authentication decorators will try to redirect the user to the login page. While this is great when you're on a webpage, when accessing the resource from any other type of client, receiving a 401 (Unauthorized) is the preferred response and the one that is returned when using Simple REST authentication decorators.

The other item I want to mention is the ``signature_required`` authentication decorator. Many APIs use a secure signature to identify a user and so we've added an authentication decorator that will add that functionality to your resources. The ``signature_required`` decorator will expect that an `HMAC`_, as defined by `RFC 2104`_, is sent with the HTTP request in order to authenticate the user. An HMAC is built around a user's secret key and so there needs to be a way for the ``signature_required`` decorator to get that secret key and that is done by providing the decorator with a function that takes a Django `HttpRequest`_ object and any number of positional and keyword arguments as defined by the URLconf. Let's take a look at an example of using the ``signature_required`` decorator with our sample resource code::

    # ===============
    # views.py
    # ===============

    import shelve
    import json

    from django.http import HttpResponse

    from rest import Resource
    from rest.exceptions import HttpError
    from rest.auth.decorators import signature_required

    def secret_key(request, *args, **kwargs):
        user = User.objects.get(pk=kwargs.get('uid'))
        return user.secret_key

    @signature_required(secret_key)
    class MyResource(Resource):

        def get(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            data = dict(db)
            db.close()
            return HttpResponse(json.dumps(data), content_type='application/json', status=200)

        def post(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            name = request.POST.get('name', '')
            db[name] = True
            db.sync()
            db.close()
            return HttpResponse(status=201)

        def delete(self, request, name):
            db = shelve.open('/tmp/db')
            if not db.has_key(str(name)):
                db.close()
                raise HttpError('Name does not exist', status=404)
            del(db[name])
            db.sync()
            db.close()
            return HttpResponse(status=200)

There's also another decorator called ``auth_required`` that works in the same manner as the ``signature_required`` (meaning that it takes a function that returns a secret key as well) but that requires that the user is either logged in or has a valid signature before granting them access to the resource.

Finally, if you're using the ``signature_required`` or ``auth_required`` decorator in your code and need a little extra help debugging your resources, specifically you need help generating a secure signature, Simple REST provides a custom command called ``urlencode`` that takes a set of data as key/value pairs and an optional secret key and returns a URL encoded string that you can copy and paste directly into a cURL command or other helpful tool such as the `REST Console`_ for Chrome. An example of how to use the ``urlencode`` command is listed below::

    % python manage.py urlencode --secret-key=test foo=1 bar=2 baz=3 name='Maxwell Hammer'
    bar=2&name=Maxwell+Hammer&baz=3&sig=623251d0a98d5eb5a284ff0d2683a5e6cd3b03545fc02ac6bd0bcfb4259f5779&t=1343939956&foo=1


###############
Form Validation
###############

If you want to use a form to validate the data in a REST request (e.g., a POST to create a new resource) you can run into some problems using Django's ModelForm class. Specifically, let's assume that you have a model that has several optional attributes with default values specified. If you send a request to create a new instance of this class but only include data for a handful of the optional attributes, you'd expect that the form object you create would not fail validation since saving the object would mean that the new record would simply end up with the default values for the missing attributes. This is, however, not the case with Django's ModelForm class. It is expecting to see all of the data in every request and will fail if any is missing.

To solve this issue, the Simple REST framework provides a ``ModelForm`` class in ``rest.forms`` that inherits from Django's ``ModelForm`` and initializes the incoming request with the default values from the underlying model object for any missing attributes. This allows the form validation to work correctly and for the new object to be saved with only a portion of the full set of attributes sent within the request. To use the class, simply import it instead of the normal Django ``ModelForm`` and have your form class inherit from it instead of Django's.

########
Upcoming
########

Keep on the lookout for updates to the framework. While it was originally created with the idea of providing just the bare minimum needed to use Django's class-based views for creating RESTful APIs, there are still a few nice features that we are in the process of adding that we think will compliment the framework well while still being true to our minimalist ideals. The most exciting of these updates will be the addition of automatic content negotiation for responses returned from resources.


.. _Tastypie: http://tastypieapi.org/
.. _Piston: https://bitbucket.org/jespern/django-piston/wiki/Home
.. _Django REST: http://django-rest-framework.org/
.. _class based views: https://docs.djangoproject.com/en/dev/topics/class-based-views/
.. _Django docs suggest: https://docs.djangoproject.com/en/dev/topics/class-based-views/#decorating-class-based-views
.. _HMAC: http://en.wikipedia.org/wiki/Hash-based_message_authentication_code
.. _RFC 2104: http://tools.ietf.org/html/rfc2104
.. _HttpRequest: https://docs.djangoproject.com/en/dev/ref/request-response/#httprequest-objects
.. _REST Console: http://restconsole.com
