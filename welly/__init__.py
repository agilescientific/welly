#!/usr/bin/env python
# -*- coding: utf 8 -*-
"""
==================
welly
==================
"""
from .well import Well
from .header import Header
from .curve import Curve
from .location import Location
from .crs import CRS
from . import tools

__all__ = [
           'Well',
           'Header',
           'Curve',
           'Location',
           'CRS',
           'tools',  # Various classes in here
          ]


__version__ = "unknown"
try:
    from ._version import __version__
except ImportError:
    pass
