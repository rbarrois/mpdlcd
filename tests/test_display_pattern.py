# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import unittest

from mpdlcd import display_fields, display_pattern


class DisplayPatternTests(unittest.TestCase):
    def parse(self, lines):
        registry = display_fields.FieldRegistry()
        pattern = display_pattern.ScreenPattern(lines=lines, field_registry=registry)
        pattern.parse()
        return pattern

    def select_field(self, field_class, fields):
        candidates = [field for field in fields if isinstance(field, field_class)]
        self.assertEqual(1, len(candidates))
        return candidates[0]

    def test_simple_pattern(self):
        pattern = self.parse([
            """{state} {song format=%(artist)s} {elapsed}""",
        ])
        self.assertEqual(1, len(pattern.line_fields))
        self.assertEqual(5, len(pattern.widgets))
        self.assertCountEqual(
            [
                display_fields.StateField,
                display_fields.FixedText,
                display_fields.SongField,
                display_fields.ElapsedTimeField,
                display_fields.FixedText,
            ],
            [type(field) for field in pattern.widgets],
        )

        # Check parsed attributes
        field = self.select_field(display_fields.SongField, pattern.widgets)
        self.assertEqual("%(artist)s", field.format)

    def test_multiple_options(self):
        pattern = self.parse([
            """{state} {song format=%(artist)s,speed=2} {elapsed}""",
        ])
        self.assertEqual(1, len(pattern.line_fields))
        self.assertEqual(5, len(pattern.widgets))
        self.assertCountEqual(
            [
                display_fields.StateField,
                display_fields.FixedText,
                display_fields.SongField,
                display_fields.ElapsedTimeField,
                display_fields.FixedText,
            ],
            [type(field) for field in pattern.widgets],
        )

        # Check parsed attributes
        field = self.select_field(display_fields.SongField, pattern.widgets)
        self.assertEqual("%(artist)s", field.format)
        self.assertEqual(2, field.speed)

    def test_quoting(self):
        pattern = self.parse([
            """{state} {song format="%(artist)s - %(title)s"} {elapsed}""",
        ])
        self.assertEqual(1, len(pattern.line_fields))
        self.assertEqual(5, len(pattern.widgets))
        self.assertCountEqual(
            [
                display_fields.StateField,
                display_fields.FixedText,
                display_fields.SongField,
                display_fields.ElapsedTimeField,
                display_fields.FixedText,
            ],
            [type(field) for field in pattern.widgets],
        )

        # Check parsed attributes
        field = self.select_field(display_fields.SongField, pattern.widgets)
        self.assertEqual("%(artist)s - %(title)s", field.format)

    def test_multiple_quotes(self):
        pattern = self.parse([
            """{state} {song format="%(artist)s - %(title)s",speed=2,padding=" - "} {elapsed}""",
        ])
        self.assertEqual(1, len(pattern.line_fields))
        self.assertEqual(5, len(pattern.widgets))
        self.assertCountEqual(
            [
                display_fields.StateField,
                display_fields.FixedText,
                display_fields.SongField,
                display_fields.ElapsedTimeField,
                display_fields.FixedText,
            ],
            [type(field) for field in pattern.widgets],
        )

        # Check parsed attributes
        field = self.select_field(display_fields.SongField, pattern.widgets)
        self.assertEqual("%(artist)s - %(title)s", field.format)
        self.assertEqual(2, field.speed)
        self.assertEqual(" - ", field.padding)
