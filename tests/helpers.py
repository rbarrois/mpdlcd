# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois


import contextlib
import logging


@contextlib.contextmanager
def debug(logger='mpdlcd', level=logging.DEBUG):  # pragma: no cover
    """Simple helper for punctual debug.

    Adds a StreamHandler with level 'debug' (or something else)
    to the target logger, then restores state.

    Usage:
        from . import helpers
        with helpers.debug():
            run_some_code()
    """
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(logger)
    old_level = logger.level
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    logger.addHandler(handler)

    yield

    logger.removeHandler(handler)
    logger.setLevel(old_level)
