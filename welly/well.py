#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines wells.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import lasio

from . import utils
from .fields import las_fields
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
        """
        Generic initializer for now.
        """
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

    @classmethod
    def from_lasio_well(cls, l, remap=None, funcs=None):
        """
        If you already have the lasio object.
        """
        # Build a dict of curves.
        params = {}
        for field, (sect, code) in las_fields['curve'].items():
            params[field] = utils.lasio_get(getattr(l, sect),
                                            code,
                                            remap=remap,
                                            funcs=funcs)

        curves = {c.mnemonic: Curve.from_lasio_curve(c, **params)
                  for c in l.curves}

        # Build a dict of the other well data.
        params = {'las': l,
                  'uwi': utils.lasio_get(l, 'well', 'UWI', 'value'),
                  'header': Header.from_lasio_well(l.well, remap=remap, funcs=funcs),
                  'location': Location.from_lasio_well(l.well, remap=remap, funcs=funcs),
                  'curves': curves,
                  }
        for field, (sect, code) in las_fields['well'].items():
            params[field] = utils.lasio_get(getattr(l, sect),
                                            code,
                                            remap=remap,
                                            funcs=funcs)

        # Pass into __init__() to instatiate the object.
        return cls(params)

    @classmethod
    def from_las(cls, fname, remap=None, funcs=None):
        """
        Wraps lasio.
        """
        l = lasio.read(fname)

        # Pass to other constructor.
        return cls.from_lasio_well(l, remap=remap, funcs=funcs)
