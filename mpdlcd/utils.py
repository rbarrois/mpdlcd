# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

import functools
import logging
import time


class AutoRetryCandidate(object):
    """Base class for objects wishing to use the @auto_retry decorator.

    Attributes:
        _retry_logger (logging.Logger): where to log connection failures
        retry_attempts (int): Maximum number of connection retries
        retry_wait (int): The initial time to wait between retries
        retry_backoff (int): Amount by which wait time should be multiplied
            after each failure
    """

    def __init__(self, retry_backoff, retry_wait, retry_attempts, logger=None,
            *args, **kwargs):
        if retry_backoff <= 1:
            raise ValueError('retry_backoff should be greater than 1.')
        self.retry_backoff = retry_backoff

        if retry_wait <= 0:
            raise ValueError('retry_wait should be positive.')
        self.retry_wait = retry_wait

        if retry_attempts < 0:
            raise ValueError('retry_attempts should be positive or zero')
        self.retry_attempts = retry_attempts

        if not logger:
            logger=logging.getLogger(self.__class__.__module__)
        self._retry_logger = logger

        super(AutoRetryCandidate, self).__init__(*args, **kwargs)


def auto_retry(fun):
    """Decorator for retrying method calls, based on instance parameters."""

    @functools.wraps(fun)
    def decorated(instance, *args, **kwargs):
        """Wrapper around a decorated function."""
        remaining_tries = instance.retry_attempts
        current_wait = instance.retry_wait
        retry_backoff = instance.retry_backoff
        last_error = None

        while remaining_tries >= 0:
            try:
                return fun(*args, **kwargs)
            except socket.error as e:
                last_error = e
                instance._retry_logger.warning('Connection failed: %s', e)

            remaining_tries -= 1
            if remaining_tries == 0:
                # Last attempt
                break

            # Wait a bit
            time.sleep(current_wait)
            current_wait *= retry_backoff

        # All attempts failed, let's raise the last error.
        raise last_error

    return decorated


