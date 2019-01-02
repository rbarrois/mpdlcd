#!/usr/bin/python
# Copyright (c) 2011-2015 Raphaël Barrois

import codecs
import os
import re
import sys

from setuptools import find_packages, setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


PACKAGE = 'mpdlcd'


setup(
    name='mpdlcd',
    version=get_version(PACKAGE),
    description="Display MPD status on a lcdproc server.",
    long_description=codecs.open(os.path.join(root_dir, 'README.rst'), 'r', 'utf-8').read(),
    author='Raphaël Barrois',
    author_email='raphael.barrois+mpdlcd@polytechnique.org',
    url='http://github.com/rbarrois/mpdlcd',
    download_url="http://pypi.python.org/pypi/mpdlcd/",
    keywords=['MPD', 'lcdproc', 'lcd'],
    packages=find_packages(exclude=['tests']),
    scripts=['bin/mpdlcd'],
    license='MIT',
    setup_requires=[
        'setuptools>=0.8',
    ],
    install_requires=[
        'python_mpd2',
    ],
    tests_require=[],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Sound/Audio',
    ],
    test_suite='tests',
)

