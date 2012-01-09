# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

import logging
import mpd


logger = logging.getLogger(__name__)

STATE_PLAY = 'play'
STATE_STOP = 'stop'


class MPDClient(object):

    def __init__(self, host='localhost', port='6600'):
        self._client = mpd.MPDClient()
        self._connected = False
        self.host = host
        self.port = port

    def connect(self):
        if not self._connected:
            logger.info('Connecting to MPD server at %s:%s', self.host, self.port)
            self._client.connect(host=self.host, port=self.port)
            self._connected = True

    @property
    def status(self):
        return self._client.status()

    @property
    def random(self):
        logger.debug('Fetching MPD random state')
        return self.status['random'] == 1

    @property
    def repeat(self):
        logger.debug('Fetchin MPD repeat state')
        return self.status['repeat'] == 1

    @property
    def elapsed(self):
        logger.debug('Fetching MPD elapsed time')
        time = self.status.get('time')
        if time:
            return time.split(':')[0]
        else:
            return None

    @property
    def total(self):
        logger.debug('Fetching MPD total time')
        time = self.status.get('time')
        if time:
            return time.split(':')[0]
        else:
            return None

    @property
    def state(self):
        logger.debug('Fetching MPD state')
        return self.status['state']

    @property
    def current_song(self):
        logger.debug('Fetching MPD song information')
        return MPDSong(**self._client.currentsong())


class MPDSong(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def format(self, fmt='{artist} - {title}'):
        return fmt.format(
                title=self.title,
                artist=self.artist,
                )
