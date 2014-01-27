# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import logging
import mpd
import time
import socket


from mpdlcd import utils


logger = logging.getLogger(__name__)

STATE_PLAY = 'play'
STATE_STOP = 'stop'


class MPDError(Exception):
    pass


class MPDConnectionError(MPDError):
    pass


class MPDClient(utils.AutoRetryCandidate):

    def __init__(self, host='localhost', port='6600', password=None, *args, **kwargs):
        super(MPDClient, self).__init__(*args, **kwargs)
        self._client = mpd.MPDClient()
        self._connected = False
        self.host = host
        self.port = port
        self.password = password

    def _decode_text(self, text):
        # MPD protocol states that all data is UTF-8 encoded.
        # Ref: http://www.musicpd.org/doc/protocol/ch01s02.html
        return unicode(text, 'utf8')

    def _decode_text_or_list(self, text_or_list):
        """Takes a 'text or list' and normalizes it to a UTF-8-decoded list."""
        # mpd2._read_objects returns dicts whose values may be text or lists.
        if isinstance(text_or_list, list):
            return [self._decode_text(item) for item in text_or_list]
        else:
            return [self._decode_text(text_or_list)]

    def _decode_dict(self, data):
        return dict(
            (k, self._decode_text_or_list(v)) for k, v in data.items())

    @utils.auto_retry
    def connect(self):
        if not self._connected:
            logger.info(u'Connecting to MPD server at %s:%s', self.host, self.port)
            self._client.connect(host=self.host, port=self.port)
            if self.password:
                self._client.password(self.password)
            self._connected = True

    @property
    @utils.auto_retry
    def status(self):
        return self._client.status()

    @property
    def random(self):
        logger.debug(u'Fetching MPD random state')
        return self.status['random'] == 1

    @property
    def repeat(self):
        logger.debug(u'Fetchin MPD repeat state')
        return self.status['repeat'] == 1

    def _parse_time(self, time):
        try:
            return int(time)
        except ValueError:
            return None

    @property
    def elapsed(self):
        logger.debug(u'Fetching MPD elapsed time')
        time = self.status.get('time')
        if time:
            return self._parse_time(time.split(':')[0])
        else:
            return None

    @property
    def total(self):
        logger.debug(u'Fetching MPD total time')
        time = self.status.get('time')
        if time:
            return self._parse_time(time.split(':')[-1])
        else:
            return None

    @property
    def elapsed_and_total(self):
        logger.debug(u'Fetching MPD elapsed and total time')
        time = self.status.get('time')
        if time and ':' in time:
            elapsed, total = time.split(':', 1)
            return self._parse_time(elapsed), self._parse_time(total)
        else:
            return (None, None)

    @property
    def state(self):
        logger.debug(u'Fetching MPD state')
        state = self.status['state']
        logger.debug(u'MPD state: %r', state)
        return state

    @property
    @utils.auto_retry
    def current_song(self):
        logger.debug(u'Fetching MPD song information')
        song_tags = self._decode_dict(self._client.currentsong())
        logger.debug(u'MPD currentsong: %r', song_tags)
        return MPDSong(**song_tags)


class SongTag(object):
    """A song tag.

    Attributes:
        name (str): name of the tag
        default (str): default text for the tag
        alternate_tags (str list): alternate fields from which this tag may be
            filled
    """
    def __init__(self, name, default=u"", *alternate_tags):
        self.name = name
        self.default = default
        self.alternate_tags = alternate_tags

    def get(self, tags):
        """Find an adequate value for this field from a dict of tags."""
        # Try to find our name
        value = tags.get(self.name, u'')

        for name in self.alternate_tags:
            # Iterate of alternates until a non-empty value is found
            value = value or tags.get(name, u'')

        # If we still have nothing, return our default
        value = value or self.default
        return value


class MPDSong(object):
    BASE_TAGS = (
        SongTag('artist', u"<Unknown>", 'albumartist', 'composer', 'performer'),
        SongTag('title', u"<Unknown>", 'name'),
        SongTag('name', u"<Unknown>", 'title'),
        SongTag('time', u"--:--"),
        SongTag('file', u"<Unknown>"),
    )

    def __init__(self, **kwargs):
        # Each tag may be multi-valued, keep only the first one.
        self.tags = dict((k.lower(), v[0]) for k, v in kwargs.items())
        for tag in self.BASE_TAGS:
            self.tags[tag.name] = tag.get(self.tags)

        for name, value in self.tags.items():
            setattr(self, name, value)

    def __nonzero__(self):
        """If no song is playing, we won't have an ID."""
        return 'id' in self.tags

    def format(self, fmt=u'{artist} - {title}'):
        return fmt.format(**self.tags)
