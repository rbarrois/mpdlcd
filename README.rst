mpdlcd
======

.. image:: https://secure.travis-ci.org/rbarrois/mpdlcd.svg?branch=master
    :target: https://travis-ci.org/rbarrois/mpdlcd/

.. image:: https://img.shields.io/pypi/v/mpdlcd.svg
    :target: https://pypi.org/project/mpdlcd/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/mpdlcd.svg
    :target: https://pypi.org/project/mpdlcd/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/wheel/mpdlcd.svg
    :target: https://pypi.org/project/mpdlcd/
    :alt: Wheel status

.. image:: https://img.shields.io/pypi/l/mpdlcd.svg
    :target: https://pypi.org/project/mpdlcd/
    :alt: License

MPDLcd is a small adapter which will display the status of a MPD server on a LCD screen, through lcdproc.

It allows defining various layouts depending on LCD size, with fix or moving parts.


Running
-------

The command line is quite simple::

    # Connect to the local mpd and lcdproc, logging to stderr
    mpdlcd


Other options are possible::

    mpdlcd --mpd=mpd.example.org:1234 --lcdproc=lcd.example.org:456 \
            --syslog --syslog-facility=user2 --loglevel=debug --lcdd_debug

Please use ``mpdlcd --help`` or ``man mpdlcd`` for a full help description.


Installing
----------

The simplest way to install MPDLcd is to use your distribution's packages.
It requires the and ``python_mpd2`` Python library.


Gentoo
""""""

Use the Sunrise overlay at http://overlays.gentoo.org/proj/sunrise/browser/app-misc/mpdlcd


Debian/Ubuntu
"""""""""""""

1. Install the ``python-mpd`` package:

   .. code-block:: sh

      apt-get install python-mpd

2. Install ``mpdlcd`` from PIP:

   .. code-block:: sh

      pip install mpdlcd


Other
"""""

If it hasn't been packaged for your distribution yet, you can also install from sources by hand:

.. code-block::

  pip install mpdlcd

This will pull in the ``python_mpd2`` Python library.

Example initd scripts are provided in the *initd/* folder.


Reporting issues
----------------

Issues should be reported on https://github.com/rbarrois/mpdlcd/issues.

Crash report should include:

- Current MPD status (playing, stopped, ...)
- Custom ``/etc/mpdlcd.conf`` file content
- Current MPDLcd version, as given by ``mpdlcd --version``
- Full output from running MPDLcd in debug mode, typically with the following options::

    mpdlcd --no-syslog --logfile=- --loglevel=debug


Contact
-------

The main channel for reporting issues would be https://github.com/rbarrois/issues.

I'm also available:

- By email, at raphael.barrois+mpdlcd@polytechnique.org
- On IRC, as Xelnor on irc.freenode.net
