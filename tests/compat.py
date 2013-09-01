# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import sys


if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

if sys.version_info[0] >= 3:
    import unittest.mock as mock
else:
    import mock
