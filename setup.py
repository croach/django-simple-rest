try:
    from setuptools import setup, find_packages
except ImportError:
    import sys
    print >>sys.stderr, "Error: setuptools is required to install this package."
    sys.exit(1)


__version__ = '1.4.0'
__author__ = 'Christopher Roach'
__email__ = 'croach@freshplum.com'
__license__ = 'MIT'

setup(
    name='django-simple-rest',
    version=__version__,
    author=__author__,
    author_email=__email__,
    description='A drop dead simple package for creating RESTful APIs on top of Django',
    long_description=open('README.rst').read(),
    url='https://github.com/freshplum/django-simple-rest',
    packages=find_packages(),
    install_requires=['setuptools', 'mimeparse'],
    zip_safe=False,
    keywords='rest,django,api',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
