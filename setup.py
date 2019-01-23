#!/usr/bin/env python

from setuptools import setup, find_packages
import os, static_website_activitypub

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'Readme.rst')) as f:
    long_description = f.read()
    
setup(
    name='static-website-activitypub',
    version=static_website_activitypub.version,
    description='Wraps a static website generator with an ActivityPub client-to-server implementation',
    long_description=long_description,
    author='Niall Douglas',
    url='http://pypi.python.org/pypi/static-website-activitypub',
    packages=['static_website_activitypub'],
    package_data={'static_website_activitypub' : ['../LICENSE']},
    test_suite='tests',
    entry_points={
        'console_scripts': [ 'static-website-activitypub=static_website_activitypub:main' ]
    },
    install_requires=['ConfigArgParse'],
    license='Apache',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: CherryPy',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)