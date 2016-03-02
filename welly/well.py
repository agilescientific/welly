#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines wells.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import matplotlib.pyplot as plt
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
        rows += s.format(k="data", v=list(self.data.keys()))
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
        curve_params = {}
        for field, (sect, code) in las_fields['curve'].items():
            curve_params[field] = utils.lasio_get(l,
                                                  sect,
                                                  code,
                                                  remap=remap,
                                                  funcs=funcs)

        curves = {c.mnemonic: Curve.from_lasio_curve(c, **curve_params)
                  for c in l.curves}

        # Build a dict of the other well data.
        params = {'las': l,
                  'header': Header.from_lasio(l, remap=remap, funcs=funcs),
                  'location': Location.from_lasio(l, remap=remap, funcs=funcs),
                  'data': curves,
                  }
        for field, (sect, code) in las_fields['well'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)

        return cls(params)

    @classmethod
    def from_las(cls, fname, remap=None, funcs=None):
        """
        Wraps lasio.
        """
        l = lasio.read(fname)

        # Pass to other constructor.
        return cls.from_lasio(l, remap=remap, funcs=funcs)


    def to_las(fname):
        """
        Save a LAS file.
        """

        pass

    def add_curves_from_las(self, fname, remap=None, funcs=None):
        """
        Given a lasio object, add curves from it.
        """
        l = lasio.read(fname)

        # Pass to other constructor.
        return self.add_curves_from_lasio(l, remap=remap, funcs=funcs)

    def add_curves_from_lasio(self, l, remap=None, funcs=None):
        """
        Given a lasio object, add curves from it.
        """
        params = {}
        for field, (sect, code) in las_fields['curve'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)

        curves = {c.mnemonic: Curve.from_lasio_curve(c, **params)
                  for c in l.curves}

        # Update data with new curves.
        # This will clobber anything with the same key!
        self.data.update(curves)

    def plot(self, legend=None, tracks=None):
        """
        Plot some well data, e.g. as a composite log.

        slegend is the legend of the striplog

        clegend is the legend of the curves

        If legend is None, you should get random colours.

        If tracks is None, you get a plot of every log and every striplog in
        the legend. If legend and tracks are None, you get everything.

        Tracks is a list of mnemonics. It can include lists, to plot multiple
        curves into a track.

        Let's just do curves for now.

        e.g. tracks = ['GR', 'RHOB', ['DT', 'DTS']]
        """
        # Set tracks to 'all' if it's None.
        tracks = tracks or list(self.data.keys())

        # Set up the figure.
        ntracks = len(tracks)
        fig, axarr = plt.subplots(1, ntracks,
                                  figsize=(2*ntracks, 13),
                                  sharey=True)

        for i, track in enumerate(tracks):
            try:  # ...treating as a plottable objectself.
                self.data[track].plot(ax=axarr[i], legend=legend)
            except TypeError:  # ...it's a list.
                for u in track:
                    self.data[u].plot(ax=axarr[i], legend=legend)

        return None
