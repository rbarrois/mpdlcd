# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

from .compat import unittest

from mpdlcd import display_fields


class FieldRegistryTestCase(unittest.TestCase):
    def setUp(self):
        display_fields.FieldRegistry._REGISTRY = {}

    def test_register(self):
        class SomeField(object):
            def __init__(self, ref):
                self.ref = ref

        display_fields.FieldRegistry.register_field('some_field', SomeField)

        reg = display_fields.FieldRegistry()

        field = reg.create('some_field')
        self.assertEqual(0, field.ref)
        self.assertEqual(SomeField, field.__class__)

    def test_increment_ref(self):
        """Field reference should increase with each create() call."""
        class SomeField(object):
            def __init__(self, ref):
                self.ref = ref

        display_fields.FieldRegistry.register_field('some_field', SomeField)

        reg = display_fields.FieldRegistry()

        field = reg.create('some_field')
        self.assertEqual(0, field.ref)
        self.assertEqual(SomeField, field.__class__)

        field2 = reg.create('some_field')
        self.assertEqual(1, field2.ref)
        self.assertEqual(SomeField, field2.__class__)

    def test_create_kwargs(self):
        """Keyword arguments for create() should pass to Field.__init__."""
        class SomeField(object):
            def __init__(self, ref, foo=2):
                self.ref = ref
                self.foo = foo

        display_fields.FieldRegistry.register_field('some_field', SomeField)

        reg = display_fields.FieldRegistry()

        field = reg.create('some_field')
        self.assertEqual(0, field.ref)
        self.assertEqual(2, field.foo)
        self.assertEqual(SomeField, field.__class__)

        field2 = reg.create('some_field', foo=4)
        self.assertEqual(1, field2.ref)
        self.assertEqual(4, field2.foo)
        self.assertEqual(SomeField, field2.__class__)

    def test_register_field_decorator(self):
        """The @register_field decorator should guess the name."""
        @display_fields.register_field
        class SomeField(object):
            base_name = 'some_field'
            def __init__(self, ref):
                self.ref = ref

        reg = display_fields.FieldRegistry()

        field = reg.create('some_field')
        self.assertEqual(0, field.ref)
        self.assertEqual(SomeField, field.__class__)

    def test_register_field_decorator_noname(self):
        """The @register_field decorator fails when 'base_name' is missing."""

        with self.assertRaises(AttributeError):
            @display_fields.register_field
            class SomeField(object):
                """Fake field without a base_name."""

    def test_register_noname(self):
        """Registering without name should raise an error."""
        class SomeField(object):
            base_name = 'some_field'

        self.assertRaises(display_fields.FieldRegistryError,
            display_fields.FieldRegistry.register_field, '', SomeField)

    def test_register_conflict(self):
        """Registering two different fields with the same name should fail."""
        class SomeField(object):
            pass

        display_fields.FieldRegistry.register_field('some_field', SomeField)

        class AltField(object):
            pass

        self.assertRaises(display_fields.FieldRegistryError,
            display_fields.FieldRegistry.register_field, 'some_field', AltField)

    def test_register_twice_no_conflict(self):
        """Registering the same field twice shouldn't fail."""
        class SomeField(object):
            base_name = 'some_field'
            def __init__(self, ref):
                self.ref = ref

        display_fields.FieldRegistry.register_field('some_field', SomeField)
        display_fields.FieldRegistry.register_field('some_field', SomeField)

        reg = display_fields.FieldRegistry()

        field = reg.create('some_field')
        self.assertEqual(0, field.ref)
        self.assertEqual(SomeField, field.__class__)

    def test_invalid_name(self):
        """Creating an invalid field should fail."""
        reg = display_fields.FieldRegistry()
        self.assertRaises(display_fields.FieldRegistryError, reg.create, 'foo')



if __name__ == '__main__':  # pragma: no cover
    unittest.main()
