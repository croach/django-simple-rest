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

There's nothing to it, it works just like you'd expect it to---assuming you're familiar with Django's `class based views`_. Before we get started though, let's create a base project and application for us to play around with.

####################
Sample Project Setup
####################

The code in the rest of this document will assume that you're using Django 1.4 or greater (you can follow along using Django 1.3, but your directory structure will be slightly different form the one below) and that you've created a project called ``simple_rest_example`` and an application within it called ``phonebook``.

Once you've created your sample project and application, you'll need to add a new URLconf to the phonebook application where we will add all of our routes for the duration of this tutorial. Then, update the URLconf in the ``simple_rest_example`` folder to include the URLconf you've just created. This will allow us to do all of our work in the phonebook app from here on out. The ``urls.py`` file in your ``simple_rest_example`` folder should now look like the following::

    # =============================
    # simple_rest_example/views.py
    # =============================

    from django.conf.urls import patterns, include, url

    urlpatterns = patterns('',
        url(r'^phonebook/', include('phonebook.urls')),
    )

If you've set everything up correctly, you should have a directory structure that matches the one shown below::

    simple_rest_example
            |
            |___ simple_rest_sample
            |           |___ __init__.py
            |           |___ settings.py
            |           |___ urls.py
            |           |___ wsgi.py
            |
            |___ phonebook
            |       |
            |       |___ __init__.py
            |       |___ models.py
            |       |___ tests.py
            |       |___ urls.py
            |       |___ views.py
            |
            |___ manage.py

Finally, we're going to create a new model class called ``Contact`` and create our database to hold all of the contacts in our phonebook. Open up ``phonebook/models.py`` and update it to match the following::

    # =====================
    # phonebook/models.py
    # =====================

    from django.db import models

    class Contact(models.Model):
        fname = models.CharField(max_length=30)
        lname = models.CharField(max_length=30)
        phone_number = models.CharField(max_length=12)

Once you've added a new model, update the ``settings.py`` file in the ``simple_rest_example`` directory to use a sqlite database named phonebook.db and run the ``manage.py syncdb`` command to create the database. Make sure to add an administrator account so that we'll have something to use later on when discussing the authentication options provided by the Simple REST framework.

###################
Creating a Resource
###################

Now that you've got your development environment set up properly, let's take a look at an example of how to use the Simple REST framework to create a dead simple phonebook application.

The sample code below shows one example of how we could create a simple resource for managing lists of contacts::

    # ====================
    # phonebook/views.py
    # ====================

    from django.http import HttpResponse
    from django.core import serializers

    from simple_rest import Resource

    from .models import Contact


    class Contacts(Resource):

        def get(self, request, contact_id=None, **kwargs):
            json_serializer = serializers.get_serializer('json')()
            if contact_id:
                contacts = json_serializer.serialize(Contact.objects.filter(pk=contact_id))
            else:
                contacts = json_serializer.serialize(Contact.objects.all())
            return HttpResponse(contacts, content_type='application/json', status=200)

        def post(self, request, *args, **kwargs):
            Contact.objects.create(
                fname=request.POST.get('fname'),
                lname=request.POST.get('lname'),
                phone_number=request.POST.get('phone_number'))
            return HttpResponse(status=201)

        def delete(self, request, contact_id):
            contact = Contact.objects.get(pk=contact_id)
            contact.delete()
            return HttpResponse(status=200)

In the example code above, we imported the ``Resource`` class, which simply inherits from Django's ``View`` class and provides the extra sauce to get all of the HTTP methods working properly. Then, we create a new class that inherits from the ``Resource`` class, and we add a function for each HTTP method that we want to handle. The only requirement is that the function name must match the HTTP method name, so `get` or `GET` for a GET call and so forth. Simple enough, right? So, let's see how to hook up our resource::

    # ===================
    # phonebook/urls.py
    # ===================

    from django.conf.urls import patterns, include, url

    from .views import Contacts

    urlpatterns = patterns('',
        # Allow access to the contacts resource collection
        url(r'^contacts/?$', Contacts.as_view()),

        # Allow access to a single contact resource
        url(r'^contacts/(?P<name>[a-zA-Z-]+)/?$', Contacts.as_view()),
    )

The sample ``urls.py`` above shows exactly how we would go about creating the URL patterns for our example resource. Again, if you're familiar with Django class based views, there should be no surprises here.

##############
Authentication
##############

So what about authentication? Well, you could simply use the ``method_decorator`` function as the `Django docs suggest`_ to decorate each method in your resource with the appropriate authentication decorator. Assuming you want the entire resource protected, you could also decorate the result of the call to ``as_view`` in the URLconf. Both of these options are completely valid and you can feel free to use them, this framework does provide another option, however.

In the ``simple_rest.auth.decorators`` module you'll find decorators there that you can use to add authentication to your resources. Let's take a look at a few examples using our sample code from above::

    # ====================
    # phonebook/views.py
    # ====================

    from django.http import HttpResponse
    from django.core import serializers

    from simple_rest import Resource
    from simple_rest.auth.decorators import login_required, admin_required

    from .models import Contact


    class Contacts(Resource):

        def get(self, request, contact_id=None, **kwargs):
            json_serializer = serializers.get_serializer('json')()
            if contact_id:
                contacts = json_serializer.serialize(Contact.objects.filter(pk=contact_id))
            else:
                contacts = json_serializer.serialize(Contact.objects.all())
            return HttpResponse(contacts, content_type='application/json', status=200)

        @login_required
        def post(self, request, *args, **kwargs):
            Contact.objects.create(
                fname=request.POST.get('fname'),
                lname=request.POST.get('lname'),
                phone_number=request.POST.get('phone_number'))
            return HttpResponse(status=201)

        @admin_required
        def delete(self, request, contact_id):
            contact = Contact.objects.get(pk=contact_id)
            contact.delete()
            return HttpResponse(status=200)

Assuming that we don't mind if anyone sees our collection of contacts, we can leave ``get`` method as is, but let's assume that we have strict requirements for who can add and delete contacts. Assuming that only registered users can add contacts, we add the ``login_required`` decorator to the ``post`` method. We don't mind if any our members add new contacts, but we don't want a contact to be accidentally deleted from our database, so let's decorate that one differently with the ``admin_required`` decorator. ``admin_required`` simply makes sure that the user is logged in and is also a super user before they will be granted access to the decorated view method.

Now, this can get a bit tedious if we have lots of resources and they all tend to have the same authentication requirements. To make a little less tedious, the authentication decorators work on both classes and methods. In the example below we're adding a superuser requirement to every method offered by the resource simply by decorating the resource class::

    # ====================
    # phonebook/views.py
    # ====================

    from django.http import HttpResponse
    from django.core import serializers

    from simple_rest import Resource
    from simple_rest.auth.decorators import admin_required

    from .models import Contact


    @admin_required
    class Contacts(Resource):

        def get(self, request, contact_id=None, **kwargs):
            json_serializer = serializers.get_serializer('json')()
            if contact_id:
                contacts = json_serializer.serialize(Contact.objects.filter(pk=contact_id))
            else:
                contacts = json_serializer.serialize(Contact.objects.all())
            return HttpResponse(contacts, content_type='application/json', status=200)

        def post(self, request, *args, **kwargs):
            Contact.objects.create(
                fname=request.POST.get('fname'),
                lname=request.POST.get('lname'),
                phone_number=request.POST.get('phone_number'))
            return HttpResponse(status=201)

        def delete(self, request, contact_id):
            contact = Contact.objects.get(pk=contact_id)
            contact.delete()
            return HttpResponse(status=200)

Before we leave the topic of authentication decorators there are two more items to take a look at.

First, when using the framework's authentication decorators, the correct RESTful response is returned whenever authentication fails. The typical Django authentication decorators will try to redirect the user to the login page. While this is great when you're on a webpage, when accessing the resource from any other type of client, receiving a 401 (Unauthorized) is the preferred response and the one that is returned when using Simple REST authentication decorators. For that reason alone, you should prefer the Simple REST authentication decorators over Django's built in ones when creating a RESTful API.

The other item to discuss is the ``signature_required`` authentication decorator. Many APIs use a secure signature to identify and the Simple REST framework provides an authentication decorator that you can use to add that functionality to your resources. The ``signature_required`` decorator will expect that an `HMAC`_, as defined by `RFC 2104`_, is sent with the HTTP request in order to authenticate the user. An HMAC is built around a user's secret key and so there needs to be a way for the ``signature_required`` decorator to get that secret key and that is done by providing the decorator with a function that takes a Django `HttpRequest`_ object and any number of positional and keyword arguments as defined by the URLconf. Let's take a look at an example of using the ``signature_required`` decorator with our sample resource code::

    # ====================
    # phonebook/views.py
    # ====================

    from django.http import HttpResponse
    from django.core import serializers

    from simple_rest import Resource
    from simple_rest.auth.decorators import signature_required

    from .models import Contact


    def secret_key(request, *args, **kwargs):
        return 'test'

    @signature_required(secret_key)
    class Contacts(Resource):

        def get(self, request, contact_id=None, **kwargs):
            json_serializer = serializers.get_serializer('json')()
            if contact_id:
                contacts = json_serializer.serialize(Contact.objects.filter(pk=contact_id))
            else:
                contacts = json_serializer.serialize(Contact.objects.all())
            return HttpResponse(contacts, content_type='application/json', status=200)

        def post(self, request, *args, **kwargs):
            Contact.objects.create(
                fname=request.POST.get('fname'),
                lname=request.POST.get('lname'),
                phone_number=request.POST.get('phone_number'))
            return HttpResponse(status=201)

        def delete(self, request, contact_id):
            contact = Contact.objects.get(pk=contact_id)
            contact.delete()
            return HttpResponse(status=200)

The ``signature_required`` decorator takes one argument, a function that, when called with an HttpRequest object and any number of positional and keyword arguments as defined by the URLconf entry for the resource, will return a string representing the secret key for the user making the request. In the example above, we created a function that returns the string 'test' no matter what arguments are passed into the function. Obviously, you don't want to use a secret key function like this in production, but for our purposes it will suffice.

To test out the ``signature_required`` decorator, you can hit any of the URLs for the Contacts resource with a ``t`` value representing a UTC POSIX timestamp for the current time and a ``sig`` value representing the HMAC signature generated from the data being sent, the timestamp, and the secret key (in this case, 'test'). If you've added 'simple_rest' to your list of ``INSTALLED_APPS``, you can use the handy ``urlencode`` command to calculate the signature and timestamp for testing your resources. The command line below shows how to generate the timestamp and signature values for a simple GET request. To test the GET call, just enter the line below into your command line and copy and paste the response to the querystring part of the URL::

    % manage.py urlencode --secret-key=test

To URL encode the request body as well, just include each piece of data as a key=value pair in the call to the ``urlencode`` command. As an example of how to do so, let's test the ``POST`` call. Run the following command in your terminal and copy the results into either the request body or the querystring portion of the URL::

    % manage.py urlencode --secret-key fname=Winston lname=Smith phone_number=555-555-5555

Finally, there's one more decorator called ``auth_required`` that works in the same manner as the ``signature_required`` (meaning that it takes a function that returns a secret key as well) but that requires that the user is either logged in or has a valid signature before granting them access to the resource.

###############
Form Validation
###############

If you want to use a form to validate the data in a REST request (e.g., a POST to create a new resource) you can run into some problems using Django's ModelForm class. Specifically, let's assume that you have a model that has several optional attributes with default values specified. If you send a request to create a new instance of this class but only include data for a handful of the optional attributes, you'd expect that the form object you create would not fail validation since saving the object would mean that the new record would simply end up with the default values for the missing attributes. This is, however, not the case with Django's ModelForm class. It is expecting to see all of the data in every request and will fail if any is missing.

To solve this issue, the Simple REST framework provides a ``ModelForm`` class in ``simple_rest.forms`` that inherits from Django's ``ModelForm`` and initializes the incoming request with the default values from the underlying model object for any missing attributes. This allows the form validation to work correctly and for the new object to be saved with only a portion of the full set of attributes sent within the request. To use the class, simply import it instead of the normal Django ``ModelForm`` and have your form class inherit from it instead of Django's.

To give it a try, let's add another field to the ``Contact`` model class in ``phonebook/models.py`` to hold an honorific for a contact. We'll make this field optional and make the default title be '(no title)'. With these new changes, the ``models.py`` file should match the one listed below::

    # ====================
    # phonebook/models.py
    # ====================

    from django.db import models

    class Contact(models.Model):
        title = models.CharField(max_length=10, default='(no title)')
        fname = models.CharField(max_length=30)
        lname = models.CharField(max_length=30)
        phone_number = models.CharField(max_length=12)

Once, you've updated the ``models.py`` file, either delete and rerun ``syncdb`` or add the new column to the phonebook_contact table by hand. Then, create a new form class called ``ContactForm`` in the ``phonebook/views.py`` file and set its model to ``Contact``. Then you can remove the code to create a new contact in the ``post`` method and replace it with code that uses the new ``Contactform`` class. The result should be similar to the following::

    # ====================
    # phonebook/views.py
    # ====================

    from django.http import HttpResponse
    from django.core import serializers

    from simple_rest import Resource
    from simple_rest.auth.decorators import signature_required
    from simple_rest.forms import ModelForm

    from .models import Contact


    def secret_key(request, *args, **kwargs):
        return 'test'


    class ContactForm(ModelForm):
        class Meta:
            model = Contact


    @signature_required(secret_key)
    class Contacts(Resource):

        def get(self, request, contact_id=None, **kwargs):
            json_serializer = serializers.get_serializer('json')()
            if contact_id:
                contacts = json_serializer.serialize(Contact.objects.filter(pk=contact_id))
            else:
                contacts = json_serializer.serialize(Contact.objects.all())
            return HttpResponse(contacts, content_type='application/json', status=200)

        def post(self, request, *args, **kwargs):
            form = ContactForm(request.POST.copy())
            if not form.is_valid():
                return HttpResponse(status=409)
            form.save()
            return HttpResponse(status=201)

        def delete(self, request, contact_id):
            contact = Contact.objects.get(pk=contact_id)
            contact.delete()
            return HttpResponse(status=200)


###################
Content Negotiation
###################

A key factor to having a truly RESTful API is the decoupling of your resources from their representation. In other words, whether or not a resource is delivered as XML or JSON shouldn't be part of the resource itself. This is where `content negotiation`_ comes into play. It provides a standardized way for a single URI to serve a resource while still allowing the user to request several different representations of that resource. Content negotiation is part of the HTTP specification and the mechanism it provides the client for requesting a representation is through the Accept header. In the Accept header the client gives a list of acceptable representations and the server works out the best possible representation of the resource to deliver according to what is available on the server and desired representations requested.

The Simple Rest framework provides a mechanism by which you can add content negotiation to your resources. This functionality is provided in the `RESTfulResponse`_ class. The RESTfullResponse class is an implementation of the method described by James Bennett in his article "`Another take on content negotiation`_". The way it works is simple, create an instance of the class and use it as a decorator on your resource. The rest of this section will take a look at a few examples to show the different options available to you when using the RESTfulResonse class to provide multiple representations of your resource.

The first example below shows the absolute simplest way to use the RESTfulResponse class to provide a JSON only representation of a resource. JSON is one of the most popular resource representations (arguably the most popular, at least for APIs being created today) and, as a result, the RESTfulResponse class provides support for it by default. So, to provide a JSON representation of your resource using the RESTfulResponse class, you simply create an instance of it and decorate your resource just like the example shows below::

    # ===================
    # phonebook/views.py
    # ===================

    import shelve

    from django.http import HttpResponse

    from rest import Resource
    from rest.response import RESTfulResponse


    class MyResource(Resource):

        @RESTfulResponse()
        def get(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            data = dict(db)
            db.close()
            return data

        def post(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            name = request.POST.get('name', '')
            db[name] = True
            db.sync()
            db.close()
            return HttpResponse(status=201)

Notice that in the ``get`` method above we are returning a simple python dict rather than the usual HttpResponse object. When using content negotiation on your resources, simple serializable python objects are the typical response. If you return an HttpResponse object it will simply bypass the content negotiation and just return the response object as is.

In the example above we only decorated the ``get`` method, but an instance of RESTfulResponse works just as the authentication decorators we saw earlier in that they can be used to decorate methods or full classes. In the next example we decorate the entire resource class and, though we can continue to return an HttpResponse object, if we want all of our methods to enjoy the benefits provided by the RESTfulResponse decorator, we need to change what they return from an HttpResponse object to a serializable python object. The code below shows how you can do that for the simple example we saw above::

    # ===================
    # phonebook/views.py
    # ===================

    import shelve

    from django.http import HttpResponse

    from rest import Resource
    from rest.response import RESTfulResponse


    @RESTfulResponse()
    class MyResource(Resource):

        def get(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            data = dict(db)
            db.close()
            return data

        def post(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            name = request.POST.get('name', '')
            db[name] = True
            db.sync()
            db.close()
            return None, 201

One thing to notice in the code above is that the ``post`` method returns a tuple. That's because when we use the RESTfulResponse decorator it's expected that we are returning a tuple where the first element is the object to be serialized and returned to the client and the second element is the status code of the response. If only a serializable object is returned (as we've done in the ``get`` method), the default status code of 200 (OK) is used. If, on the other hand, you'd like to return an empty response with just the HTTP Response Code set to signify the success or failure of the operation, you can simply return ``None`` for the data object and the desired status code as the second element in the tuple. In ``post`` method in the code sample above we see an example of this. Since performing a POST on our resource creates a new instance of that resource we want to return a 201 () signifying that a new resource was succesfully created and the response body can be empty.

The last sample below shows how to provide multiple different representations of

Finally, content negotiation doesn't really do much if you only provide a single representation of your resource. The question then becomes: how do we provide more than just the default JSON representation? The answer to that question is that we pass into the RESTfulResponse constructor a dict that maps mime types to either a python callable that can be called on the data object to transform it into the designated representation or a string that points to a template that will be used to produce the desired representation. In this example we'll be using a template to transform the resource into an XML representation.

The first step is to create our XML template. The RESTfulResponse decorator will automatically provide any data returned from the resource to the template under the name ``context``. In the exmaple code below we sort the people in the database according to last name and return a person element that has fname and lname subelements::

    <?xml version="1.0"?>

    {% with people=context.values|dictsort:"lname" %}
    <phonebook>
      {% for person in people %}
          <person>
            <fname>{{ person.fname }}</fname>
            <lname>{{ person.lname }}</lname>
          </person>
      {% endfor %}
    </phonebook>
    {% endwith %}

Once we've got the template created, we just need to create a new RESTfulResponse decorator with the correct mime type mapped to the template. The code below shows how to do that; keep in mind that JSON is the default, so our mime type mapping dict doesn't need to contain an entry for JSON::

    # ===================
    # phonebook/views.py
    # ===================

    import shelve

    from django.http import HttpResponse

    from rest import Resource
    from rest.response import RESTfulResponse


    json_or_xml = RESTfulResponse({'application/xml': 'myresource.xml'})

    @json_or_xml
    class MyResource(Resource):

        def get(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            data = dict(db)
            db.close()
            return data

        def post(self, request, *args, **kwargs):
            db = shelve.open('/tmp/db')
            fname = request.POST.get('fname', '')
            lname = request.POST.get('lname', '')
            key = '%s_%s' % (lname.lower(), fname.lower())
            db[key] = {
                'fname': fname,
                'lname': lname
            }
            db.sync()
            db.close()
            return None, 201



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
.. _content negotation: http://en.wikipedia.org/wiki/Content_negotiation
.. _Another take on content negotiation: http://www.b-list.org/weblog/2008/nov/29/multiresponse/
.. _RESTFulResponse: https://github.com/freshplum/django-simple-rest/blob/master/rest/response.py
