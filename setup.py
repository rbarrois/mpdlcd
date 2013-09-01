#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import os
import re
import sys

from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    path_components = package_components + ['__init__.py']
    with open(os.path.join(root_dir, *path_components)) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


def parse_requirements(requirements_file):
    with open(requirements_file, 'r') as f:
        return [line for line in f if line.strip() and not line.startswith('#')]


if sys.version_info[0:2] < (2, 7):
    extra_tests_require = ['unittest2', 'mock']
elif sys.version_info[0] < 3:
    extra_tests_require = ['mock']
else:
    extra_tests_require = []


PACKAGE = 'mpdlcd'
REQUIREMENTS_PATH = 'requirements.txt'


setup(
    name='mpdlcd',
    version=get_version(PACKAGE),
    description="Display MPD status on a lcdproc server.",
    author='Raphaël Barrois',
    author_email='raphael.barrois+mpdlcd@polytechnique.org',
    url='http://github.com/rbarrois/mpdlcd',
    download_url="http://pypi.python.org/pypi/mpdlcd/",
    keywords=['MPD', 'lcdproc', 'lcd'],
    packages=['mpdlcd'],
    scripts=['bin/mpdlcd'],
    license='MIT',
    setup_requires=[
        'setuptools>=0.8',
    ],
    install_requires=parse_requirements(REQUIREMENTS_PATH),
    tests_require=[] + extra_tests_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Multimedia :: Sound/Audio',
    ],
    test_suite='tests',
)

