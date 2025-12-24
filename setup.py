#!/usr/bin/env python
# setup.py
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

"""Install script for ConfigObj"""

# Copyright (C) 2005-2014:
# (name) : (email)
# Michael Foord: fuzzyman AT voidspace DOT org DOT uk
# Mark Andrews: mark AT la-la DOT com
# Nicola Larosa: nico AT tekNico DOT net
# Rob Dennis: rdennis AT gmail DOT com
# Eli Courtwright: eli AT courtwright DOT org

# This software is licensed under the terms of the BSD license.
# http://opensource.org/licenses/BSD-3-Clause
import io
import os
import re
import sys
from contextlib import closing

from setuptools import setup

if sys.version_info[0] < 2:
    print('for Python versions < 3 use bashconfigparser '
          'version 5.0.8')
    sys.exit(1)

__here__ = os.path.abspath(os.path.dirname(__file__))

NAME = 'bashconfigparser'
MODULES = []
PACKAGES = ['bashconfigparser']
DESCRIPTION = 'Config file reading, writing and validation.'
URL = 'https://github.com/Cranix-Solutions/bashconfigparser'

VERSION = ''
with closing(open(os.path.join(__here__, 'src', PACKAGES[0], '_version.py'), 'r')) as handle:
    for line in handle.readlines():
        if line.startswith('__version__'):
            VERSION = re.split('''['"]''', line)[1]
assert re.match(r"[0-9](\.[0-9]+)", VERSION), "No semantic version found in 'bashconfigparser._version'"

LONG_DESCRIPTION = """**BashConfigParser** is a simple but powerful config file reader and writer:
    BashConfigParser is desined to read bash style config files which contains comments an value assignments
        /etc/sysconfig/*

"""

try:
    with io.open('CHANGES.rst', encoding='utf-8') as handle:
        LONG_DESCRIPTION += handle.read()
except EnvironmentError as exc:
    # Build / install anyway
    print("WARNING: Cannot open/read CHANGES.rst due to {}".format(exc))

CLASSIFIERS = [
    # Details at http://pypi.python.org/pypi?:action=list_classifiers
    'Development Status :: 6 - Mature',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Operating System :: OS Independent',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

AUTHOR = 'Peter Varkolxy'

AUTHOR_EMAIL = 'pvarkoly@cephalix.eu'

KEYWORDS = "config, bash, dictionary, application, admin, sysadmin, configuration".split(', ')

project = dict(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    py_modules=MODULES,
    package_dir={'': 'src'},
    packages=PACKAGES,
    python_requires='>=3.7',
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    license='BSD-3-Clause',
)

if __name__ == '__main__':
    setup(**project)
