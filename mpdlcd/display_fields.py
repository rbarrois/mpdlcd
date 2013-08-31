# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

"""Handle fields on screen."""


import collections
import logging

from . import utils

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
            logger.debug(u'Registring field %s', name)
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
    target_hooks = []

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
        """Add the field to the screen.

        The 'screen' object is a lcdproc Screen object, and left/top indicate
        the topleft corner attributed to the field by the global pattern.

        This method must return the generated widget.
        """
        raise NotImplementedError()

    def register_hooks(self):
        """Register hooks to be notified of field changes.

        Should return a list of fields whose information is watched.

        Yields:
            (str, set) tuples: the name of hooks of interest,
                and the list of sub-hooks to watch in each.
        """
        for hook in self.target_hooks:
            yield hook, set()

    def hook_changed(self, hook_name, widget, new_data):
        """Handle a hook upate."""
        if hook_name == 'song':
            self.song_changed(widget, new_data)
        elif hook_name == 'state':
            self.state_changed(widget, new_data)
        elif hook_name == 'elapsed_and_total':
            elapsed, total = new_data
            self.time_changed(widget, elapsed, total)

    def song_changed(self, widget, new_song):
        pass

    def state_changed(self, widget, new_state):
        pass

    def time_changed(self, widget, elapsed, total):
        pass

    def set_widget_text(self, widget, text):
        """Sets the text of a widget, taking into account server charset.

        Args:
            widget (lcdproc.Widget): widget whose text should be set
            text (unicode): text to set
        """
        widget.set_text(widget.screen.server.encode(text))

    def __repr__(self):
        return '<Field %s (%d)>' % (self.name, self.width)


@register_field
class FixedText(Field):
    base_name = 'fixed'

    def __init__(self, text, **kwargs):
        super(FixedText, self).__init__(width=len(text), **kwargs)
        self.text = text
    
    def add_to_screen(self, screen, left, top):
        return screen.add_string_widget(self.name,
            screen.server.encode(self.text), left, top)


@register_field
class StateField(Field):
    base_name = 'state'
    target_hooks = ['state']

    def __init__(self, **kwargs):
        super(StateField, self).__init__(width=1, **kwargs)

    def add_to_screen(self, screen, left, top):
        return screen.add_icon_widget(self.name, x=left, y=top, name='STOP')

    def state_changed(self, widget, new_state):
        name = MPD_TO_LCDD_MAP.get(new_state, MPD_STOP)
        logger.debug(u'Setting widget %s to %r', widget.ref, name)
        widget.set_name(name)


class BaseTimeField(Field):
    target_hooks = ['state', 'elapsed_and_total']

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
            logger.debug(u'Setting widget %s to %r', widget.ref, txt)
            widget.set_text(txt)


@register_field
class ElapsedTimeField(BaseTimeField):
    base_name = 'elapsed'

    def time_changed(self, widget, elapsed, total):
        txt = self._format_time(elapsed)
        logger.debug(u'Setting widget %s to %r', widget.ref, txt)
        widget.set_text(txt)


@register_field
class TotalTimeField(BaseTimeField):
    base_name = 'total'

    def time_changed(self, widget, elapsed, total):
        txt = self._format_time(total)
        logger.debug(u'Setting widget %s to %r', widget.ref, txt)
        widget.set_text(txt)


@register_field
class RemainingTimeField(BaseTimeField):
    base_name = 'remaining'

    def time_changed(self, widget, elapsed, total):
        if total is not None and elapsed is not None:
            remaining = total - elapsed
        else:
            remaining = None
        txt = self._format_time(remaining)
        logger.debug(u'Setting widget %s to %r', widget.ref, txt)
        widget.set_text(txt)


@register_field
class BitRateField(Field):
    base_name = 'bitrate'
    target_hooks = ['status']

    def _format_bitrate(self, bitrate=0):
        bitrate = int(bitrate)
        return '%3d' % bitrate

    def __init__(self, **kwargs):
        width = len(self._format_bitrate())
        super(BitRateField, self).__init__(width=width, **kwargs)

    def add_to_screen(self, screen, left, top):
        return screen.add_string_widget(self.name,
            self._format_bitrate(), x=left, y=top)

    def hook_changed(self, hook_name, widget, new_data):
        if hook_name == 'status':
            self.status_changed(widget, new_data)
        super(BitRateField, self).hook_changed(hook_name, widget, new_data)

    def status_changed(self, widget, new_status):
        txt = self._format_bitrate(new_status.get('bitrate') or 0)
        logger.debug(u"Setting widget %r to %r", widget.ref, txt)
        widget.set_text(txt)


@register_field
class SongField(Field):
    base_name = 'song'
    target_hooks = ['song']

    def __init__(self, format=u'', width=-1, speed=2, **kwargs):
        self.format = format
        self.watched_fields = utils.extract_pattern(format)
        self.speed = int(speed)
        super(SongField, self).__init__(width=width, **kwargs)

    def add_to_screen(self, screen, left, top):
        return screen.add_scroller_widget(self.name,
            left=left, top=top, right=left + self.width - 1, bottom=top,
            speed=self.speed, text=' ' * self.width)

    def register_hooks(self):
        """Override: register watched_fields as subhooks of the 'song' hook."""
        base_subhooks = dict(super(SongField, self).register_hooks())
        base_subhooks['song'] |= set(self.watched_fields)
        return base_subhooks.items()

    @classmethod
    def _song_dict(cls, song):
        fields = collections.defaultdict(lambda: u'')
        fields.update(song.tags)
        return fields

    def song_changed(self, widget, new_song):
        if new_song:
            txt = self.format % self._song_dict(new_song)
        else:
            txt = u''
        logger.debug(u'Setting widget %s to %r', widget.ref, txt)
        self.set_widget_text(widget, txt)
