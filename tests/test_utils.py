# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

from .compat import unittest

from mpdlcd import utils


class ExtractPatternTest(unittest.TestCase):
    def test_empty_format(self):
        self.assertEqual([], utils.extract_pattern(''))

    def test_newstyle_format(self):
        self.assertEqual([], utils.extract_pattern('{foo}, {0}'))

    def test_non_dict(self):
        self.assertEqual([], utils.extract_pattern('%s %d'))

    def test_success(self):
        self.assertEqual(['aa', 'bbb'],
            utils.extract_pattern('%(aa)s %(bbb)d %%(c)s'))

    def test_repeated(self):
        self.assertEqual(['aa'], utils.extract_pattern('%(aa)s %(aa)d %(aa)s'))

    def test_partial(self):
        """Interpolation fails mid-way."""
        self.assertEqual(['aa'], utils.extract_pattern('%(aa)s %d %(bbb)d'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
