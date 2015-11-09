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

__all__ = [
           'Well',
           'Header',
           'Curve',
          ]


__version__ = "unknown"
try:
    from ._version import __version__
except ImportError:
    pass
