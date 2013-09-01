# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import sys


if sys.version_info[:2] < (2, 7):  # pragma: no cover
    import unittest2 as unittest
else:  # pragma: no cover
    import unittest

if sys.version_info[0] >= 3:  # pragma: no cover
    import unittest.mock as mock
else:  # pragma: no cover
    import mock
