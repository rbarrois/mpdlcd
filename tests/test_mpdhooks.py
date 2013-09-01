# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

from .compat import unittest

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


class MPDHookTest(unittest.TestCase):
    class FakeClient(object):
        def __init__(self, data):
            self.data = data

    class FakeHook(mpdhooks.MPDHook):
        name = 'fake'
        def fetch(self, client):
            return client.data

    class FakeSubHook(FakeHook):
        def extract_key(self, data, key):
            return data[key]

    def test_first_change(self):
        client = self.FakeClient(42)
        hook = self.FakeHook()
        changed, new = hook.handle(client)

        self.assertTrue(changed)
        self.assertEqual(42, new)

    def test_repeated_change(self):
        client = self.FakeClient(42)
        hook = self.FakeHook()
        changed, new = hook.handle(client)

        self.assertTrue(changed)
        self.assertEqual(42, new)

        client2 = self.FakeClient(13)
        changed2, new2 = hook.handle(client2)

        self.assertTrue(changed2)
        self.assertEqual(13, new2)

    def test_unchanged(self):
        client = self.FakeClient(42)
        hook = self.FakeHook()
        changed, new = hook.handle(client)

        self.assertTrue(changed)
        self.assertEqual(42, new)

        changed2, new2 = hook.handle(client)
        self.assertFalse(changed2)
        self.assertIsNone(new2)

    def test_default_subhook(self):
        client = self.FakeClient({'': 42, 'fake': 13})
        hook = self.FakeSubHook()
        hook.handle(client)  # Register initial state

        client2 = self.FakeClient({'': 42, 'fake': 24})

        # The value associated with 'fake' changed, should yield update.
        changed, new = hook.handle(client2)
        self.assertTrue(changed)
        self.assertEqual({'': 42, 'fake': 24}, new)


    def test_subhook_first_change(self):
        client = self.FakeClient({'x': 42, 'y': 13})
        hook = self.FakeSubHook()
        changed, new = hook.handle(client, ('x',))

        self.assertTrue(changed)
        self.assertEqual({'x': 42, 'y': 13}, new)

    def test_subhook_repeated_change(self):
        client = self.FakeClient({'x': 42, 'y': 13})
        hook = self.FakeSubHook()
        changed, new = hook.handle(client, ('x',))

        self.assertTrue(changed)
        self.assertEqual({'x': 42, 'y': 13}, new)

        client2 = self.FakeClient({'x': 13, 'y': 42})
        changed2, new2 = hook.handle(client2, ('x',))

        self.assertTrue(changed2)
        self.assertEqual({'x': 13, 'y': 42}, new2)

    def test_subhook_unchanged(self):
        client = self.FakeClient({'x': 42, 'y': 13})
        hook = self.FakeSubHook()
        changed, new = hook.handle(client, ('x',))

        self.assertTrue(changed)
        self.assertEqual({'x': 42, 'y': 13}, new)

        # Only a non-watched field changes.
        client2 = self.FakeClient({'x': 42, 'y': 24})
        changed2, new2 = hook.handle(client2, ('x',))
        self.assertFalse(changed2)
        self.assertIsNone(new2)


class SpecificHooksTest(unittest.TestCase):
    class FakeClient(object):
        def __init__(self, status=None, state=None, elapsed_and_total=None, current_song=None):
            self.status = status
            self.state = state
            self.elapsed_and_total = elapsed_and_total
            self.current_song = current_song

    def test_status_hook(self):
        hook = mpdhooks.StatusHook()

        client = self.FakeClient(status={'bitrate': 42})
        changed, new = hook.handle(client)
        self.assertTrue(changed)
        self.assertEqual({'bitrate': 42}, new)

        client2 = self.FakeClient(status={'bitrate': 13})
        changed2, new2 = hook.handle(client2)
        self.assertTrue(changed2)
        self.assertEqual({'bitrate': 13}, new2)

        # Another field changes
        client3 = self.FakeClient(state='play', status={'bitrate': 13})
        changed3, new3 = hook.handle(client3)
        self.assertFalse(changed3)
        self.assertIsNone(new3)

    def test_state_hook(self):
        hook = mpdhooks.StateHook()

        client = self.FakeClient(state='stop')
        changed, new = hook.handle(client)
        self.assertTrue(changed)
        self.assertEqual('stop', new)

        client2 = self.FakeClient(state='play')
        changed2, new2 = hook.handle(client2)
        self.assertTrue(changed2)
        self.assertEqual('play', new2)

        # Another field changes
        client3 = self.FakeClient(state='play', status={'bitrate': 13})
        changed3, new3 = hook.handle(client3)
        self.assertFalse(changed3)
        self.assertIsNone(new3)

    def test_elapsed_and_total_hook(self):
        hook = mpdhooks.ElapsedAndTotalHook()

        client = self.FakeClient(elapsed_and_total=(0, 0))
        changed, new = hook.handle(client)
        self.assertTrue(changed)
        self.assertEqual((0, 0), new)

        client2 = self.FakeClient(elapsed_and_total=(0.1, 10))
        changed2, new2 = hook.handle(client2)
        self.assertTrue(changed2)
        self.assertEqual((0.1, 10), new2)

        # Another field changes
        client3 = self.FakeClient(elapsed_and_total=(0.1, 10), state='pause')
        changed3, new3 = hook.handle(client3)
        self.assertFalse(changed3)
        self.assertIsNone(new3)

    def test_song_hook(self):
        hook = mpdhooks.SongHook()
        class FakeSong(object):
            def __init__(self, id=42, **extra):
                self.id = id
                for k, v in extra.items():
                    setattr(self, k, v)

        # Default is 'no song'
        client = self.FakeClient(current_song={})
        changed, new = hook.handle(client)
        self.assertFalse(changed)
        self.assertIsNone(new)

        # New song loaded
        new_song = FakeSong()
        client2 = self.FakeClient(current_song=new_song)
        changed2, new2 = hook.handle(client2)
        self.assertTrue(changed2)
        self.assertEqual(new_song, new2)

        # Song id changes
        other_song = FakeSong(id=13)
        client3 = self.FakeClient(current_song=other_song)
        changed3, new3 = hook.handle(client3)
        self.assertTrue(changed3)
        self.assertEqual(other_song, new3)

        # Another field changes
        client4 = self.FakeClient(current_song=other_song, state='play')
        changed4, new4 = hook.handle(client4)
        self.assertFalse(changed4)
        self.assertIsNone(new4)

        # Check for subfields
        other_song_full = FakeSong(id=13, title="other", artist="someone")
        client5 = self.FakeClient(current_song=other_song_full)
        changed5, new5 = hook.handle(client5, ('title', 'artist'))
        self.assertTrue(changed5)
        self.assertEqual(other_song_full, new5)

        # Only the id changes, not watched fields
        other_song_full2 = FakeSong(id=42, title="other", artist="someone")
        client6 = self.FakeClient(current_song=other_song_full2)
        changed6, new6 = hook.handle(client6, ('title', 'artist'))
        self.assertFalse(changed6)
        self.assertIsNone(new6)

        # A watched field changes.
        # Typically happens on radio streams.
        third_song_full = FakeSong(id=13, title="new!!", artist="another")
        client7 = self.FakeClient(current_song=third_song_full)
        changed7, new7 = hook.handle(client7, ('title', 'artist'))
        self.assertTrue(changed7)
        self.assertEqual(third_song_full, new7)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
