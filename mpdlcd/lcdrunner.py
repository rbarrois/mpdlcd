# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

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
        self.hooks = {}
        self.subhooks = {}
        self.client = client

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

    def setup_pattern(self, patterns, hook_registry):
        self.pattern = patterns[self.screen.height]
        self.pattern.parse()
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
