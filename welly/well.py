#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines wells.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import lasio

from .curve import Curve
from .header import Header
from .location import Location


class WellError(Exception):
    """
    Generic error class.
    """
    pass


class Well(object):
    """
    Well contains everything about the well.
    """
    def __init__(self, params):
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

    @classmethod
    def from_las(cls, fname):
        """Wraps lasio
        """
        params = {}

        l = lasio.read(fname)

        curves = [Curve(c, basis=l['DEPT']) for c in l.curves]

        params = {'las': l,
                  'header': Header.from_lasio_well(l.well),
                  'location': Location(l.well),
                  'curves': curves,
                  }

        return cls(params)
