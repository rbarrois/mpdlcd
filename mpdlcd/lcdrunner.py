# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

import datetime
import logging
import time

import mpdwrapper
from lcdproc import server


logger = logging.getLogger(__name__)


LCD_SCREEN_NAME = 'MPD'
LCD_ELAPSED_WIDGET = 'elapsed'
LCD_STATE_WIDGET = 'state'
LCD_ARTIST_WIDGET = 'artist'
LCD_TITLE_WIDGET = 'title'

MPD_STOP = 'stop'
MPD_PLAY = 'play'
MPD_PAUSE = 'pause'

MPD_TO_LCDD_MAP = {
    MPD_STOP: 'STOP',
    MPD_PLAY: 'PLAY',
    MPD_PAUSE: 'PAUSE',
}


class MpdRunner(object):
    def __init__(self, client, lcd):
        self.lcd = lcd
        self.lcd.start_session()
        self.screen = self.setup_screen(LCD_SCREEN_NAME)
        self.client = client
        self._previous = {
            'song': None,
            'elapsed': None,
            'state': MPD_STOP,
        }

    def setup_screen(self, screen_name):
        logger.debug('Adding lcdproc screen %s', screen_name)
        screen = self.lcd.add_screen(screen_name)
        screen.set_heartbeat('off')
        screen.set_priority(64)

        width = self.lcd.server_info['screen_width']
        height = self.lcd.server_info['screen_height']
        logger.info('LCD screen is %dx%d', width, height)

        screen.set_width(width)
        screen.set_height(height)

        # Template is :
        # +------------------------+
        # |<artist>       <elapsed>|
        # |<title>          <state>|
        # +------------------------+

        artist_width = width - 6  # <elapsed> is 5 chars wide, plus 1 space.
        screen.add_scroller_widget(LCD_ARTIST_WIDGET,
            left=1, top=1, right=artist_width, bottom=1, speed=1,
            text=' ' * artist_width)

        screen.add_string_widget(LCD_ELAPSED_WIDGET,
            x=artist_width + 2, y=1, text='--:--')

        title_width = width - 2 # 1 for state, 1 space
        screen.add_scroller_widget(LCD_TITLE_WIDGET,
            left=1, top=2, right=title_width, bottom=2, speed=2,
            text=' ' * title_width)

        screen.add_icon_widget(LCD_STATE_WIDGET,
            x=title_width + 2, y=2, name='STOP')
        logger.info('%s screen added to lcdproc.', screen_name)
        return screen

    def update(self):
        current_song = self.client.current_song
        if current_song.id != self._previous['song']:
            self._previous['song'] = current_song.id
            logger.debug('Switching to song #%s', current_song.id)
            self.screen.widgets[LCD_ARTIST_WIDGET].set_text(current_song.artist)
            self.screen.widgets[LCD_TITLE_WIDGET].set_text(current_song.title)

        elapsed = self.client.elapsed
        if elapsed != self._previous['elapsed']:
            self._previous['elapsed'] = elapsed
            if elapsed:
                logger.debug('Updating elapsed time to %s', elapsed)
                self.screen.widgets[LCD_ELAPSED_WIDGET].set_text(
                    self._format_time(int(elapsed)))
            else:
                self.clear_elapsed()

        state = self.client.state
        if state != self._previous['state']:
            logger.debug('State changed from %s to %s',
                    self._previous['state'], state)

            self._previous['state'] = state
            self.screen.widgets[LCD_STATE_WIDGET].set_name(
                MPD_TO_LCDD_MAP.get(state, MPD_STOP))

    def clear_elapsed(self):
        logger.debug('Clearing elapsed time')
        self.screen.widgets[LCD_ELAPSED_WIDGET].set_text('--:--')

    def clear_title(self):
        logger.debug('Clearing song title')
        self._clear_widget(self.screen.widgets[LCD_TITLE_WIDGET])

    def clear_artist(self):
        logger.debug('Clearing song artist')
        self._clear_widget(self.screen.widgets[LCD_ARTIST_WIDGET])

    def _clear_widget(self, widget):
        widget.set_text(' ' * (widget.right - widget.left + 1) * (widget.top - widget.bottom + 1))

    def _format_time(self, seconds):
        minutes = seconds / 60
        seconds = seconds % 60
        return '%02d:%02d' % (minutes, seconds)

    def quit(self):
        logger.info('Exiting: removing screen %s', LCD_SCREEN_NAME)
        self.lcd.del_screen(LCD_SCREEN_NAME)

    def run(self):
        logger.info('Starting update loop.')
        try:
            while True:
                self.update()
                time.sleep(0.5)
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            self.quit()
