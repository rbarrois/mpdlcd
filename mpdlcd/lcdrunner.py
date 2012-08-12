# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

import datetime
import logging
import time

from lcdproc import server

from mpdlcd import utils


logger = logging.getLogger(__name__)


class LcdProcServer(server.Server):
    def __init__(self, hostname, port, charset, *args, **kwargs):
        super(LcdProcServer, self).__init__(hostname, port, *args, **kwargs)
        self.charset = charset

    def encode(self, text):
        """Helper to handle server-specific text encoding."""
        return text.encode(self.charset, 'ignore')


class MpdRunner(utils.AutoRetryCandidate):
    def __init__(self, client, lcd, lcdproc_screen, *args, **kwargs):
        super(MpdRunner, self).__init__(logger=logger, *args, **kwargs)

        self.lcd = lcd
        self.lcdproc_screen = lcdproc_screen

        # Make sure we can connect - no need to go further otherwise.
        self._connect_lcd()
        self.pattern = None
        self.screen = self.setup_screen(self.lcdproc_screen)
        self.client = client
        self._previous = {
            'song': None,
            'elapsed_and_total': None,
            'state': None,
        }

    @utils.auto_retry
    def _connect_lcd(self):
        self.lcd.start_session()

    def setup_screen(self, screen_name):
        logger.debug(u'Adding lcdproc screen %s', screen_name)
        screen = self.lcd.add_screen(screen_name)
        screen.set_heartbeat('off')
        screen.set_priority(64)

        width = self.lcd.server_info['screen_width']
        height = self.lcd.server_info['screen_height']
        logger.info(u'LCD screen is %dx%d', width, height)

        screen.set_width(width)
        screen.set_height(height)

        logger.info(u'%s screen added to lcdproc.', screen_name)
        return screen

    def setup_pattern(self, patterns):
        self.pattern = patterns[self.screen.height]
        self.pattern.parse()
        self.pattern.add_to_screen(self.screen.width, self.screen)

    @utils.auto_retry
    def update(self):
        current_song = self.client.current_song
        if current_song:
            current_song_id = current_song.id
        else:
            current_song_id = None
        if current_song_id != self._previous['song']:
            self._previous['song'] = current_song_id
            logger.debug(u'Switching to song #%s', current_song_id)
            self.pattern.song_changed(current_song)

        elapsed, total = self.client.elapsed_and_total
        if (elapsed, total) != self._previous['elapsed_and_total']:
            logger.debug(u'Updating elapsed/total time to %s/%s', elapsed, total)
            self._previous['elapsed_and_total'] = (elapsed, total)
            self.pattern.time_changed(elapsed, total)

        state = self.client.state
        if state != self._previous['state']:
            logger.debug(u'State changed from %s to %s',
                    self._previous['state'], state)
            self._previous['state'] = state
            self.pattern.state_changed(state)

    def quit(self):
        logger.info(u'Exiting: removing screen %s', self.lcdproc_screen)
        self.lcd.del_screen(self.lcdproc_screen)

    def run(self):
        logger.info(u'Starting update loop.')
        try:
            while True:
                self.update()
                time.sleep(0.5)
        except (KeyboardInterrupt, SystemExit):
            pass
        except Exception as e:
            logger.exception(u"Found exception %s, exiting.", e)
        finally:
            self.quit()
