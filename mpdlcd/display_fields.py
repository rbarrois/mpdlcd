# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

"""Handle fields on screen."""


import collections
import logging

logger = logging.getLogger(__name__)


class FieldRegistryError(Exception):
    pass


class FieldRegistry(object):
    _REGISTRY = {}

    @classmethod
    def register_field(cls, name, field_class):
        if not name:
            raise FieldRegistryError(
                "Need a name to register field %s." % field_class)
        elif name not in cls._REGISTRY:
            logger.debug('Registring field %s', name)
            cls._REGISTRY[name] = field_class
        else:
            if cls._REGISTRY[name] != field_class:
                raise FieldRegistryError(
                    "Cannot register two fields with the same name.")

    def __init__(self):
        self._counter = collections.defaultdict(lambda: 0)

    def create(self, name, **kwargs):
        if name not in self._REGISTRY:
            raise FieldRegistryError(
                "Unknown field name '%s' (available: %s)"
                % (name, ', '.join(self._REGISTRY.keys())))

        ref = self._counter[name]
        self._counter[name] += 1
        return self._REGISTRY[name](ref=ref, **kwargs)


def register_field(field_class):
    FieldRegistry.register_field(field_class.base_name, field_class)
    return field_class


MPD_STOP = 'stop'
MPD_PLAY = 'play'
MPD_PAUSE = 'pause'

MPD_TO_LCDD_MAP = {
    MPD_STOP: 'STOP',
    MPD_PLAY: 'PLAY',
    MPD_PAUSE: 'PAUSE',
}


class Field(object):
    base_name = None

    def __init__(self, ref, width=-1, **kwargs):
        assert self.base_name
        self.ref = ref
        self.width = width

    @property
    def name(self):
        return '%s-%d' % (self.base_name, self.ref)

    def is_flexible(self):
        return self.width < 0

    def add_to_screen(self, screen, left, top):
        raise NotImplementedError()

    def song_changed(self, widget, new_song):
        pass

    def state_changed(self, widget, new_state):
        pass

    def time_changed(self, widget, elapsed, total):
        pass

    def __repr__(self):
        return '<Field %s (%d)>' % (self.name, self.width)


@register_field
class FixedText(Field):
    base_name = 'fixed'

    def __init__(self, text, **kwargs):
        super(FixedText, self).__init__(width=len(text), **kwargs)
        self.text = text
    
    def add_to_screen(self, screen, left, top):
        return screen.add_string_widget(self.name, self.text,
            left, top)


@register_field
class StateField(Field):
    base_name = 'state'

    def __init__(self, **kwargs):
        super(StateField, self).__init__(width=1, **kwargs)

    def add_to_screen(self, screen, left, top):
        return screen.add_icon_widget(self.name, x=left, y=top, name='STOP')

    def state_changed(self, widget, new_state):
        name = MPD_TO_LCDD_MAP.get(new_state, MPD_STOP)
        logger.debug('Setting widget %s to %r', widget.ref, name)
        widget.set_name(name)


class BaseTimeField(Field):
    def __init__(self, **kwargs):
        super(BaseTimeField, self).__init__(width=5, **kwargs)

    @classmethod
    def _format_time(cls, seconds):
        if seconds is None:
            return '--:--'

        minutes = seconds / 60
        seconds = seconds % 60
        return '%02d:%02d' % (minutes, seconds)

    def add_to_screen(self, screen, left, top):
        return screen.add_string_widget(self.name, self._format_time(None),
            x=left, y=top)

    def state_changed(self, widget, new_state):
        if new_state not in (MPD_PLAY, MPD_PAUSE):
            txt = self._format_time(None)
            logger.debug('Setting widget %s to %r', widget.ref, txt)
            widget.set_text(txt)


@register_field
class ElapsedTimeField(BaseTimeField):
    base_name = 'elapsed'

    def time_changed(self, widget, elapsed, total):
        txt = self._format_time(elapsed)
        logger.debug('Setting widget %s to %r', widget.ref, txt)
        widget.set_text(txt)


@register_field
class TotalTimeField(BaseTimeField):
    base_name = 'total'

    def time_changed(self, widget, elapsed, total):
        txt = self._format_time(total)
        logger.debug('Setting widget %s to %r', widget.ref, txt)
        widget.set_text(txt)


@register_field
class RemainingTimeField(BaseTimeField):
    base_name = 'remaining'

    def time_changed(self, widget, elapsed, total):
        txt = self._format_time(total - elapsed)
        logger.debug('Setting widget %s to %r', widget.ref, txt)
        widget.set_text(txt)


@register_field
class SongField(Field):
    base_name = 'song'

    def __init__(self, format='', width=-1, speed=2, **kwargs):
        self.format = format
        self.speed = speed
        super(SongField, self).__init__(width=width, **kwargs)

    def add_to_screen(self, screen, left, top):
        return screen.add_scroller_widget(self.name,
            left=left, top=top, right=left + self.width - 1, bottom=top,
            speed=self.speed, text=' ' * self.width)

    @classmethod
    def _song_dict(cls, song):
        fields = collections.defaultdict(lambda: '')
        fields.update({
            'artist': song.artist,
            'title': song.title,
            'album': song.album,
            'duration': song.time,
        })
        return fields

    def song_changed(self, widget, new_song):
        txt = self.format % self._song_dict(new_song)
        logger.debug('Setting widget %s to %r', widget.ref, txt)
        widget.set_text(txt)
