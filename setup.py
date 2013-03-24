#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

from distutils.core import setup
from distutils import cmd
import os
import re

def get_version():
    version_re = re.compile(r"^__version__ = '([\w_.]+)'$")
    with open(os.path.join(os.path.dirname(__file__), 'mpdlcd', '__init__.py')) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.0'


class test(cmd.Command):
    """Run the tests for this package."""
    command_name = 'test'
    description = 'run the tests associated with the package'

    user_options = [
        ('test-suite=', None, "A test suite to run (defaults to 'tests')"),
    ]

    def initialize_options(self):
        self.test_runner = None
        self.test_suite = None

    def finalize_options(self):
        self.ensure_string('test_suite', 'tests')

    def run(self):
        """Run the test suite."""
        try:
            import unittest2 as unittest
        except ImportError:
            import unittest

        if self.verbose:
            verbosity=1
        else:
            verbosity=0

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        if self.test_suite == 'tests':
            for test_module in loader.discover('.'):
                suite.addTest(test_module)
        else:
            suite.addTest(loader.loadTestsFromName(self.test_suite))

        result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
        if not result.wasSuccessful():
            sys.exit(1)


setup(
    name='mpdlcd',
    version=get_version(),
    description="Display MPD status on a lcdproc server.",
    author='Raphaël Barrois',
    author_email='raphael.barrois+mpdlcd@polytechnique.org',
    url='http://github.com/rbarrois/mpdlcd',
    download_url="http://pypi.python.org/pypi/mpdlcd/",
    keywords=['MPD', 'lcdproc', 'lcd'],
    packages=['mpdlcd'],
    scripts=['bin/mpdlcd'],
    license='MIT',
    requires=[
        'python_mpd2',
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
    cmdclass={'test': test},
)

