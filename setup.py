import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

__version__ = '0.4.2'
__author__ = 'Christopher Roach'
__email__ = 'croach@freshplum.com'
__license__ = ''

setup(
    name='rest',
    version=__version__,
    author=__author__,
    author_email=__email__,
    description='A bare bones simple package for creating RESTful APIs on top of Django',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    zip_safe=False,
)
