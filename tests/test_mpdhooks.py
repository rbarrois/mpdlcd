# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import unittest

from mpdlcd import mpdhooks


class HookRegistryTest(unittest.TestCase):
    def setUp(self):
        mpdhooks.HookRegistry._REGISTRY = {}

    def test_register(self):
        class SomeHook(object):
            pass

        mpdhooks.HookRegistry.register_hook('some_hook', SomeHook)

        reg = mpdhooks.HookRegistry()

        hook = reg.create('some_hook')
        self.assertEqual(SomeHook, hook.__class__)

    def test_create_kwargs(self):
        """Keyword arguments for create() should pass to Hook.__init__."""
        class SomeHook(object):
            def __init__(self, foo=2):
                self.foo = foo

        mpdhooks.HookRegistry.register_hook('some_hook', SomeHook)

        reg = mpdhooks.HookRegistry()

        hook = reg.create('some_hook')
        self.assertEqual(2, hook.foo)
        self.assertEqual(SomeHook, hook.__class__)

        hook2 = reg.create('some_hook', foo=4)
        self.assertEqual(4, hook2.foo)
        self.assertEqual(SomeHook, hook2.__class__)

    def test_register_hook_decorator(self):
        """The @register_hook decorator should guess the name."""
        @mpdhooks.register_hook
        class SomeHook(object):
            name = 'some_hook'

        reg = mpdhooks.HookRegistry()

        hook = reg.create('some_hook')
        self.assertEqual(SomeHook, hook.__class__)

    def test_register_hook_decorator_noname(self):
        """The @register_hook decorator fails when 'base_name' is missing."""

        def failed_registration():
            @mpdhooks.register_hook
            class SomeHook(object):
                pass

        self.assertRaises(AttributeError,
            failed_registration)

    def test_register_noname(self):
        """Registering without name should raise an error."""
        class SomeHook(object):
            base_name = 'some_hook'

        self.assertRaises(mpdhooks.HookRegistryError,
            mpdhooks.HookRegistry.register_hook, '', SomeHook)

    def test_register_conflict(self):
        """Registering two different hooks with the same name should fail."""
        class SomeHook(object):
            pass

        mpdhooks.HookRegistry.register_hook('some_hook', SomeHook)

        class AltHook(object):
            pass

        self.assertRaises(mpdhooks.HookRegistryError,
            mpdhooks.HookRegistry.register_hook, 'some_hook', AltHook)

    def test_register_twice_no_conflict(self):
        """Registering the same hook twice shouldn't fail."""
        class SomeHook(object):
            base_name = 'some_hook'

        mpdhooks.HookRegistry.register_hook('some_hook', SomeHook)
        mpdhooks.HookRegistry.register_hook('some_hook', SomeHook)

        reg = mpdhooks.HookRegistry()

        hook = reg.create('some_hook')
        self.assertEqual(SomeHook, hook.__class__)

    def test_invalid_name(self):
        """Creating an invalid hook should fail."""
        reg = mpdhooks.HookRegistry()
        self.assertRaises(mpdhooks.HookRegistryError, reg.create, 'foo')



if __name__ == '__main__':
    unittest.main()
