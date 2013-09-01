# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import logging

logger = logging.getLogger(__name__)


class HookRegistryError(Exception):
    pass


class HookRegistry(object):
    _REGISTRY = {}

    @classmethod
    def register_hook(cls, name, hook_class):
        if not name:
            raise HookRegistryError(
                "Need a name to register hook %s." % hook_class)
        elif name not in cls._REGISTRY:
            logger.debug(u'Registring hook %s', name)
            cls._REGISTRY[name] = hook_class
        else:
            if cls._REGISTRY[name] != hook_class:
                raise HookRegistryError(
                    "Cannot register two hooks with the same name.")

    def create(self, name, **kwargs):
        if name not in self._REGISTRY:
            raise HookRegistryError(
                "Unknown hook name '%s' (available: %s)"
                % (name, ', '.join(self._REGISTRY.keys())))

        return self._REGISTRY[name](**kwargs)


def register_hook(hook_class):
    HookRegistry.register_hook(hook_class.name, hook_class)
    return hook_class


class MPDHook(object):
    """A MPD-related hook."""
    name = ''

    def __init__(self, **kwargs):
        super(MPDHook, self).__init__(**kwargs)
        self.previous_keys = {}

    def fetch(self, client):  # pragma: no cover
        return None

    def extract_key(self, data, key=''):
        """Retrieve a simple identifier for data change detection.

        Can be used if the actual data is huge.

        Args:
            data (object), the data fetched by self.fetch()
            key (str), the name of the key to fetch

        Returns:
            New value for the given key
        """
        return data

    def handle(self, client, subhooks=()):
        """Handle a new update.

        Fetches new data from the client, then compares it to the previous
        lookup.

        Returns:
            (bool, new_data): whether changes occurred, and the new value.
        """
        new_data = self.fetch(client)

        # Holds the list of updated fields.
        updated = {}

        if not subhooks:
            # We always want to compare to previous values.
            subhooks = [self.name]

        for subhook in subhooks:
            new_key = self.extract_key(new_data, subhook)
            if new_key != self.previous_keys.get(subhook):
                updated[subhook] = new_key

        if updated:
            logger.debug(u"Hook %s: data changed from %r to %r",
                self.name, self.previous_keys, updated)
            self.previous_keys.update(updated)
            return (True, new_data)

        return (False, None)


@register_hook
class StatusHook(MPDHook):
    """The whole MPD status result."""
    name = 'status'

    def fetch(self, client):
        return client.status


@register_hook
class StateHook(MPDHook):
    name = 'state'

    def fetch(self, client):
        return client.state


@register_hook
class ElapsedAndTotalHook(MPDHook):
    name = 'elapsed_and_total'

    def fetch(self, client):
        return client.elapsed_and_total


@register_hook
class SongHook(MPDHook):
    name = 'song'

    def fetch(self, client):
        return client.current_song

    def extract_key(self, data, key=''):
        """Custom ``extract_key`` to detect when any watched field changed."""
        current_song = data
        if not current_song:
            return None
        if key == self.name:
            return current_song.id
        return getattr(current_song, key, '')
