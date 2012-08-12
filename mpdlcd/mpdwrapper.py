# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

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

    def __init__(self, host='localhost', port='6600', *args, **kwargs):
        super(MPDClient, self).__init__(*args, **kwargs)
        self._client = mpd.MPDClient()
        self._connected = False
        self.host = host
        self.port = port

    def _decode_text(self, text):
        # MPD protocol states that all data is UTF-8 encoded.
        # Ref: http://www.musicpd.org/doc/protocol/ch01s02.html
        return unicode(text, 'utf8')

    def _decode_dict(self, data):
        return dict(
            (k, self._decode_text(v)) for k, v in data.items())

    @utils.auto_retry
    def connect(self):
        if not self._connected:
            logger.info(u'Connecting to MPD server at %s:%s', self.host, self.port)
            self._client.connect(host=self.host, port=self.port)
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
        return self.status['state']

    @property
    @utils.auto_retry
    def current_song(self):
        logger.debug(u'Fetching MPD song information')
        return MPDSong(**self._decode_dict(self._client.currentsong()))


class MPDSong(object):
    DEFAULTS = {
        'artist': u"<Unknown>",
        'title': u"<Unknown>",
        'album': u"<Unknown>",
        'track': u"0",
        'file': u"<Unknown>",
    }

    def __init__(self, **kwargs):
        defaults = dict(self.DEFAULTS)
        defaults.update(kwargs)
        for k, v in defaults.iteritems():
            setattr(self, k, v)

    def __nonzero__(self):
        """If no song is playing, we won't have an ID."""
        return hasattr(self, 'id')

    def format(self, fmt=u'{artist} - {title}'):
        return fmt.format(
            title=self.title,
            artist=self.artist,
        )
