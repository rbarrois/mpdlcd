# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois

import sys

PY2 = bool(sys.version_info[0] == 2)

if PY2:
    import ConfigParser as configparser
    import urlparse as urllib_parse
else:
    import configparser
    import urllib.parse as urllib_parse
