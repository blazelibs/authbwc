"""
Introduction
---------------

AuthBWC is a component for `BlazeWeb <http://pypi.python.org/pypi/BlazeWeb/>`_
applications.  It provides users, groups, permissions, related helpers
and views.  Proper integration of this component will allow applications to have
views that can only be accessed by certain users.

Includes email notifications when an account is created as well as an email
based password reset mechanism.

Questions & Comments
---------------------

Please visit: http://groups.google.com/group/blazelibs

Current Status
---------------

The code stays pretty stable, but the API may change in the future.

The `AuthBWC tip <http://bitbucket.org/rsyring/authbwc/get/tip.zip#egg=authbwc-dev>`_
is installable via `easy_install` with ``easy_install AuthBWC==dev``
"""

from setuptools import setup, find_packages

from authbwc import VERSION

setup(
    name='AuthBWC',
    version=VERSION,
    description="An authentication and authorization component for the BlazeWeb framework",
    long_description=__doc__,
    classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    ],
    author='Randy Syring',
    author_email='rsyring@gmail.com',
    url='http://bitbucket.org/rsyring/authbwc/',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'CommonBWC>=0.1.0',
        'DataGridBWC>=0.1.0',
    ],
)
