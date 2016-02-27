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
from .utils import lasio_get


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

    def _repr_html_(self):
        """
        Jupyter Notebook magic repr function.
        """
        row1 = '<tr><th style="text-align:center;" colspan="2">{}<br><small>{{}}</small></th></tr>'
        rows = row1.format(self.header.name)
        rows = rows.format(self.header.uwi)
        s = '<tr><td><strong>{k}</strong></td><td>{v}</td></tr>'
        for k, v in self.location.__dict__.items():
            rows += s.format(k=k, v=v)
        rows += s.format(k="curves", v=self.curves.keys())
        html = '<table>{}</table>'.format(rows)
        return html

    @property
    def uwi(self):
        return self.header.uwi

    @classmethod
    def from_lasio(cls, l, remap=None, funcs=None):
        """
        If you already have the lasio object.
        """
        # Build a dict of curves.

        params = {}
        for field, (sect, code) in las_fields['curve'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)

        curves = {c.mnemonic: Curve.from_lasio_curve(c, **params)
                  for c in l.curves}

        # Build a dict of the other well data.
        params = {'las': l,
                  'header': Header.from_lasio(l, remap=remap, funcs=funcs),
                  'location': Location.from_lasio(l, remap=remap, funcs=funcs),
                  'curves': curves,
                  }
        for field, (sect, code) in las_fields['well'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
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
        return cls.from_lasio(l, remap=remap, funcs=funcs)
