import pkg_resources
__version__ = pkg_resources.require('rest')[0].version

from .resource import Resource
