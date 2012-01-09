#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from distutils.core import setup
from distutils import cmd
import os
import re

def get_version():
    version_re = re.compile(r"^VERSION = '([\w_.]+)'$")
    with open(os.path.join(os.path.dirname(__file__), 'mpdlcd', '__init__.py')) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.0'


setup(
    name='mpdlcd',
    version=get_version(),
    description="Display MPD status on a lcdproc server.",
    author='Raphaël Barrois',
    author_email='raphael.barrois@polytechnique.org',
    url='http://github.com/rbarrois/mpdlcd',
    download_url="http://pypi.python.org/pypi/mpdlcd/",
    keywords=['MPD', 'lcdproc', 'lcd'],
    packages=['mpdlcd'],
    scripts=['bin/mpdlcdd'],
    license='MIT',
    requires=[
        'mpd',
        'lcdproc',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)

