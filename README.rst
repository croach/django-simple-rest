############
Installation
############

1. Install using pip or easy_install: `pip install rest` or `easy_install install rest`
2. Add the ExceptionMiddleware to the list of middleware classes (optional): MIDDLEWARE_CLASSES += ['rest.exceptions.ExceptionMiddleware']
    - This step is optional and is only needed if you wish to be able to raise the HttpError from a view
3. Add the package to the list of installed apps (optional): INSTALLED_APPS += ['rest']
    - This step is optional and is only needed if you plan on using the supplied custom django commands.
