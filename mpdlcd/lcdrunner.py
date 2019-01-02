# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import logging
import time
import unicodedata

from .vendor.lcdproc import server

from . import display_fields
from . import enums
from . import utils


logger = logging.getLogger(__name__)


class LcdProcServer(server.Server):
    def __init__(self, hostname, port, charset, *args, **kwargs):
        super(LcdProcServer, self).__init__(hostname, port, *args, **kwargs)
        self.charset = charset

    def _normalize_char(self, char):
        """Normalize a character according to the LCD charset.

        If the char exists in the charset, don't change it;
        otherwise, normalize it to ascii.

        Takes a unicode char, returns a unicode char.
        """
        try:
            char.encode(self.charset)
            return char
        except UnicodeEncodeError:
            return (
                unicodedata.normalize('NFKD', char)
                .encode('ascii', 'ignore')
                .decode('ascii')
            )

    def encode(self, text):
        """Helper to handle server-specific text encoding."""
        normalized_text = ''.join(self._normalize_char(char) for char in text)
        return normalized_text.encode(self.charset)


class MpdRunner(utils.AutoRetryCandidate):
    def __init__(
            self, client, lcd, lcdproc_screen, refresh_rate,
            backlight_on, priority_playing, priority_not_playing, *args, **kwargs):
        super(MpdRunner, self).__init__(logger=logger, *args, **kwargs)

        self.lcd = lcd
        self.lcdproc_screen = lcdproc_screen
        self.backlight_on = backlight_on
        self.priority_playing = priority_playing
        self.priority_not_playing = priority_not_playing
        self.refresh_rate = refresh_rate

        # Make sure we can connect - no need to go further otherwise.
        self._connect_lcd()
        self.pattern = None
        self.screen = self.setup_screen(self.lcdproc_screen)
        self.hooks = {}
        self.subhooks = {}
        self.client = client

    @utils.auto_retry
    def _connect_lcd(self):
        self.lcd.start_session()

    def setup_screen(self, screen_name):
        logger.debug('Adding lcdproc screen %s', screen_name)
        screen = self.lcd.add_screen(screen_name)
        screen.set_heartbeat('off')
        screen.set_priority(self.priority_playing)

        width = self.lcd.server_info['screen_width']
        height = self.lcd.server_info['screen_height']
        logger.info('LCD screen is %dx%d', width, height)

        screen.set_width(width)
        screen.set_height(height)

        logger.info('%s screen added to lcdproc.', screen_name)
        return screen

    def add_pseudo_fields(self):
        """Add 'pseudo' fields (e.g non-displayed fields) to the display."""
        fields = []
        if self.backlight_on != enums.BACKLIGHT_ON_NEVER:
            fields.append(
                display_fields.BacklightPseudoField(ref='0', backlight_rule=self.backlight_on)
            )

        fields.append(
            display_fields.PriorityPseudoField(
                ref='0',
                priority_playing=self.priority_playing,
                priority_not_playing=self.priority_not_playing,
            )
        )

        self.pattern.add_pseudo_fields(fields, self.screen)

    def setup_pattern(self, patterns, hook_registry):
        self.pattern = patterns[self.screen.height]
        self.pattern.parse()
        self.add_pseudo_fields()
        self.pattern.add_to_screen(self.screen.width, self.screen)
        self.setup_hooks(hook_registry)

    def setup_hooks(self, hook_registry):
        for hook_name, subhooks in self.pattern.active_hooks():
            hook = hook_registry.create(hook_name)
            self.hooks[hook_name] = hook
            self.subhooks[hook_name] = subhooks

    @utils.auto_retry
    def update(self):
        for hook_name, hook in self.hooks.items():
            subhooks = self.subhooks[hook_name]
            updated, new_data = hook.handle(self.client, subhooks)
            if updated:
                self.pattern.hook_changed(hook_name, new_data)

    def quit(self):
        logger.info('Exiting: removing screen %s', self.lcdproc_screen)
        self.lcd.del_screen(self.lcdproc_screen)

    def run(self):
        logger.info('Starting update loop.')
        try:
            while True:
                self.update()
                time.sleep(self.refresh_rate)
        except (KeyboardInterrupt, SystemExit):
            pass
        except Exception as e:
            logger.exception("Found exception %s, exiting.", e)
        finally:
            self.quit()
