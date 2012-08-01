from setuptools import setup, find_packages

setup(
    name='rest',
    version='0.3.0',
    author='Christopher Roach',
    author_email='croach@freshplum.com',
    description='A bare bones simple package for creating RESTful APIs on top of Django',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    zip_safe=False,
    install_requires=['distribute']
)
