#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from lcdproc import server as lcdproc_server

import ConfigParser
import logging
from logging import handlers as logging_handlers
import optparse
import socket
import time

from mpdlcd import lcdrunner
from mpdlcd import mpdwrapper
from mpdlcd import display_fields
from mpdlcd import display_pattern
from mpdlcd import utils

# General
DEFAULT_CONFIG_FILE = '/etc/mpdlcd.conf'

# Display
DEFAULT_REFRESH = 0.5
DEFAULT_LCD_SCREEN_NAME = 'MPD'
DEFAULT_PATTERN = ''

# Connection
DEFAULT_MPD_PORT = 6600
DEFAULT_LCD_PORT = 13666
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_WAIT = 3
DEFAULT_RETRY_BACKOFF = 2

# Logging
DEFAULT_SYSLOG_ENABLED = False
DEFAULT_LOGLEVEL = 'warning'
DEFAULT_SYSLOG_FACILITY = 'daemon'
DEFAULT_SYSLOG_ADDRESS = '/dev/log'
DEFAULT_LOGFILE = '-'
DEFAULT_DEBUG_MODULES = ''

BASE_CONFIG = {
    'display': {
        'refresh': ('float', DEFAULT_REFRESH),
        'lcdproc_screen': ('str', DEFAULT_LCD_SCREEN_NAME),
        'pattern': ('str', DEFAULT_PATTERN),
    },
    'connections': {
        'mpd': ('str', 'localhost:%s' % DEFAULT_MPD_PORT),
        'lcdproc': ('str', 'localhost:%s' % DEFAULT_LCD_PORT),
        'lcdd_debug': ('bool', False),
        'retry_attempts': ('int', DEFAULT_RETRY_ATTEMPTS),
        'retry_wait': ('int', DEFAULT_RETRY_WAIT),
        'retry_backoff': ('int', DEFAULT_RETRY_BACKOFF),
    },
    'logging': {
        'syslog': ('bool', DEFAULT_SYSLOG_ENABLED),
        'loglevel': ('str', DEFAULT_LOGLEVEL),
        'syslog_facility': ('str', DEFAULT_SYSLOG_FACILITY),
        'syslog_address': ('str', DEFAULT_SYSLOG_ADDRESS),
        'logfile': ('str', DEFAULT_CONFIG_FILE),
        'debug': ('str', DEFAULT_DEBUG_MODULES),
    },
}

DEFAULT_PATTERNS = [
    # One line
    """{state} {song format="%(artist)s - %(title)s"} {elapsed}""",

    # Two lines
    """{song format="%(artist)s",speed=4} {elapsed}\n"""
    """{song format="%(title)s",speed=2} {state}""",

    # Three lines
    """{song format="%(artist)s",speed=4}\n"""
    """{song format="%(album)s - %(title)s",speed=2}\n"""
    """{state}  {elapsed} / {total}""",

    # Four lines
    """{song format="%(artist)s",speed=4}\n"""
    """{song format="%(album)s",speed=4}\n"""
    """{song format="%(title)s",speed=2}\n"""
    """{elapsed}  {state}  {remaining}""",
]


logger = logging.getLogger('mpdlcd')


def _make_hostport(conn, default_host, default_port):
    """Convert a 'host:port' string to a (host, port) tuple.

    If the given connection is empty, use defaults.
    If no port is given, use the default.

    Args:
        conn (str): the string describing the target hsot/port
        default_host (str): the host to use if ``conn`` is empty
        default_port (int): the port to use if not given in ``conn``.

    Returns:
        (str, int): a (host, port) tuple.
    """

    if not conn:
        return default_host, default_port

    parts = conn.split(':', 1)
    host = parts[0]
    if len(parts) == 1:
        port = default_port
    else:
        port = parts[1]

    return host, int(port)


def _make_lcdproc(lcd_host, lcd_port, retry_config, lcdd_debug=False):
    """Create and connect to the LCDd server.

    Args:
        lcd_host (str): the hostname to connect to
        lcd_prot (int): the port to connect to
        lcdd_debug (bool): whether to enable full LCDd debug
        retry_attempts (int): the number of connection attempts
        retry_wait (int): the time to wait between connection attempts
        retry_backoff (int): the backoff for increasing inter-attempt delay

    Returns:
        lcdproc.server.Server
    """

    class ServerSpawner(utils.AutoRetryCandidate):
        """Spawn the server, using auto-retry."""

        @utils.auto_retry
        def connect(self):
            return lcdproc_server.Server(lcd_host, lcd_port, debug=lcdd_debug)

    spawner = ServerSpawner(retry_config=retry_config, logger=logger)

    try:
        return spawner.connect()
    except socket.error as e:
        logger.error('Unable to connect to lcdproc %s:%s.',
            lcd_host, lcd_port)
        raise SystemExit(1)


def _make_patterns(patterns):
    """Create a ScreenPatternList from a given pattern text.

    Args:
        pattern_txt (str list): the patterns

    Returns:
        mpdlcd.display_pattern.ScreenPatternList: a list of patterns from the
            given entries.
    """
    registry = display_fields.FieldRegistry()
    pattern_list = display_pattern.ScreenPatternList(registry)
    for pattern in patterns:
        pattern_list.add(pattern.split('\n'))
    return pattern_list


def run_forever(lcdproc='', mpd='', lcdproc_screen=DEFAULT_LCD_SCREEN_NAME,
        lcdd_debug=False,
        pattern='', patterns=[],
        retry_attempts=DEFAULT_RETRY_ATTEMPTS,
        retry_wait=DEFAULT_RETRY_WAIT,
        retry_backoff=DEFAULT_RETRY_BACKOFF):
    """Run the server.

    Args:
        lcdproc (str): the target connection (host:port) for lcdproc
        mpd (str): the target connection (host:port) for mpd
        lcdproc_screen (str): the name of the screen to use for lcdproc
        lcdd_debug (bool): whether to enable full LCDd debug
        pattern (str): the pattern to use
        patterns (str list): the patterns to use
        retry_attempts (int): number of connection attempts
        retry_wait (int): time between connection attempts
        retry_backoff (int): increase to between-attempts delay
    """
    # Compute host/ports
    lcd_host, lcd_port = _make_hostport(lcdproc, 'localhost', 13666)
    mpd_host, mpd_port = _make_hostport(mpd, 'localhost', 6600)

    # Prepare auto-retry
    retry_config = utils.AutoRetryConfig(
        retry_attempts=retry_attempts,
        retry_backoff=retry_backoff,
        retry_wait=retry_wait)

    # Setup MPD client
    mpd_client = mpdwrapper.MPDClient(mpd_host, mpd_port,
        retry_config=retry_config)

    # Setup LCDd client
    lcd = _make_lcdproc(lcd_host, lcd_port, lcdd_debug=lcdd_debug,
        retry_config=retry_config)

    # Setup connector
    runner = lcdrunner.MpdRunner(mpd_client, lcd, lcdproc_screen=lcdproc_screen,
        retry_config=retry_config)

    # Fill pattern
    if pattern:
        # If a specific pattern was given, use it
        patterns = [pattern]
    elif not patterns:
        # If no patterns were given, use the defaults
        patterns = DEFAULT_PATTERNS
    pattern_list = _make_patterns(patterns)

    runner.setup_pattern(pattern_list)

    # Launch
    mpd_client.connect()
    runner.run()

    # Exit
    logging.shutdown()


LOGLEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


def _make_parser():
    parser = optparse.OptionParser()

    # General options
    # ---------------
    parser.add_option('-c', '--config', dest='config',
            help='Read configuration from CONFIG (default: %s)' %
            DEFAULT_CONFIG_FILE, metavar='CONFIG', default=DEFAULT_CONFIG_FILE)
    # End general options

    # Display options
    # ---------------
    group = optparse.OptionGroup(parser, 'Display')
    group.add_option('--pattern', dest='pattern',
            help='Use this PATTERN (lines separated by \\n)',
            metavar='PATTERN', default='')
    group.add_option('--patterns', dest='patterns', action='append',
            help='Register a PATTERN; the actual pattern is chosen according '
            'to screen height.',
            metavar='PATTERN')
    group.add_option('--refresh', dest='refresh', type='float',
            help='Refresh the display every REFRESH seconds (default: %.1fs)' %
                    DEFAULT_REFRESH,
            metavar='REFRESH')
    group.add_option('--lcdproc-screen', dest='lcdproc_screen',
            help='Register the SCREEN_NAME lcdproc screen for mpd status '
            '(default: %s)' % DEFAULT_LCD_SCREEN_NAME,
            metavar='SCREEN_NAME')

    # End display options
    parser.add_option_group(group)

    # Connection options
    # ------------------
    group = optparse.OptionGroup(parser, 'Connection')
    group.add_option('-l', '--lcdproc', dest='lcdproc',
            help='Connect to lcdproc at LCDPROC', metavar='LCDPROC')
    group.add_option('-m', '--mpd', dest='mpd',
            help='Connect to mpd running at MPD', metavar='MPD')
    group.add_option('--lcdd-debug', dest='lcdd_debug', action='store_true',
            help='Add full debug output of LCDd commands', default=False)

    # Auto-retry
    group.add_option('--retry-attempts', dest='retry_attempts', type='int',
            help='Retry connections RETRY_ATTEMPTS times (default: %d)' %
                    DEFAULT_RETRY_ATTEMPTS,
            metavar='RETRY_ATTEMPTS')
    group.add_option('--retry-wait', dest='retry_wait', type='float',
            help='Wait RETRY_WAIT between connection attempts (default: %.1fs)' %
                    DEFAULT_RETRY_WAIT,
            metavar='RETRY_WAIT')
    group.add_option('--retry-backoff', dest='retry_backoff', type='int',
            help='Increase RETRY_WAIT by a RETRY_BACKOFF factor after each '
                'failure (default: %d)' % DEFAULT_RETRY_BACKOFF,
            metavar='RETRY_BACKOFF')

    # End connection options
    parser.add_option_group(group)

    # Logging options
    # ---------------
    group = optparse.OptionGroup(parser, 'Logging')
    group.add_option('-s', '--syslog', dest='syslog', action='store_true',
            help='Enable syslog logging (default: False)')

    group.add_option('--syslog-facility', dest='syslog_facility',
            help='Log into syslog facility FACILITY (default: %s)' %
                    DEFAULT_SYSLOG_FACILITY,
            metavar='FACILITY')

    group.add_option('--syslog-address', dest='syslog_address',
            help='Log into syslog at ADDRESS (default: %s)' %
                    DEFAULT_SYSLOG_ADDRESS,
            metavar='ADDRESS')

    group.add_option('-f', '--logfile', dest='logfile',
            help="Log into LOGFILE ('-' for stderr)", metavar='LOGFILE')

    group.add_option('--loglevel', dest='loglevel', type='choice',
            help='Logging level (%s; default: %s)' %
                    ('/'.join(LOGLEVELS.keys()), DEFAULT_LOGLEVEL),
            choices=LOGLEVELS.keys())
    group.add_option('-d', '--debug', dest='debug',
            help="Log debug output from the MODULES components",
            metavar='MODULES')

    # End logging options
    parser.add_option_group(group)

    return parser


def _setup_logging(syslog=False, syslog_facility=DEFAULT_SYSLOG_FACILITY,
        syslog_address=DEFAULT_SYSLOG_ADDRESS, logfile=DEFAULT_LOGFILE,
        loglevel=DEFAULT_LOGLEVEL, debug='', **kwargs):
    level = LOGLEVELS[loglevel]

    verbose_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s')
    quiet_formatter = logging.Formatter(
            '%(levelname)s %(name)s %(message)s')

    if syslog:
        if syslog_address and syslog_address[0] == '/':
            address = syslog_address
        else:
            address = _make_hostport(syslog_address, 'localhost', logging.SYSLOG_UDP_PORT)
        handler = logging_handlers.SysLogHandler(address, facility=syslog_facility)
        handler.setFormatter(quiet_formatter)

    elif logfile == '-':
        handler = logging.StreamHandler()
        handler.setFormatter(quiet_formatter)

    else:
        handler = logging.FileHandler(logfile, level=level)
        handler.setFormatter(verbose_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    for module in debug.split(','):
        if not module.strip():
            continue
        module_logger = logging.getLogger(module)
        module_logger.setLevel(logging.DEBUG)
        module_logger.addHandler(handler)
        module_logger.info("Enabling debug")


def _read_config(filename):
    parser = ConfigParser.RawConfigParser()
    if not parser.read(filename):
        return

    config = {}

    for section, defaults in BASE_CONFIG.iteritems():
        if section == 'patterns':
            continue

        for name, descr in defaults.iteritems():
            kind, default = descr
            if section in parser.sections() and name in parser.options(section):
                if kind == 'int':
                    value = parser.getint(section, name)
                elif kind == 'float':
                    value = parser.getfloat(section, name)
                elif kind == 'bool':
                    value = parser.getboolean(section, name)
                else:
                    value = parser.get(section, name)
            else:
                value = default
            config[name] = value

    if 'patterns' in parser.sections():
        patterns = [parser.get('patterns', opt) for opt in parser.options('patterns')]
    else:
        patterns = DEFAULT_PATTERNS
    config['patterns'] = patterns

    return config


def _extract_options(config, options, *args):
    extract = {}
    for key in args:
        extract[key] = config[key]
        option = getattr(options, key)
        if option is not None:
            extract[key] = option
    return extract


def main(argv):
    parser = _make_parser()
    options, args = parser.parse_args(argv)
    base_config = _read_config(options.config)
    if options.loglevel == 'debug':
        print "Base config: %s" % base_config
        print "With overrides: %s" % _extract_options(base_config, options, *base_config.keys())

    _setup_logging(**_extract_options(base_config, options,
        'syslog', 'syslog_facility', 'syslog_address',
        'logfile', 'loglevel', 'debug'))
    run_forever(**_extract_options(base_config, options,
        'lcdproc', 'mpd', 'lcdproc_screen', 'lcdd_debug', 'pattern', 'patterns',
        'retry_attempts', 'retry_backoff', 'retry_wait'))
