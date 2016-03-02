#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines wells.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import datetime

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
        for field, (sect, code) in las_fields['data'].items():
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
                  'data': curves}

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

    def to_lasio(self, basis=None):
        # Create an empty lasio object.
        l = lasio.LASFile()
        l.well.DATE = str(datetime.datetime.today())

        # Deal with header.
        for obj, dic in las_fields.items():
            if obj == 'data':
                continue
            for attr, (sect, item) in dic.items():
                value = getattr(getattr(self, obj), attr, None)
                try:
                    getattr(l, sect)[item].value = value
                except:
                    h = lasio.HeaderItem(item, "", value, "")
                    getattr(l, sect)[item] = h

        # Add a depth basis.
        try:
            if basis is None:
                basis = self.data.get('DEPT', self.data.get('DEPTH', None))
            l.add_curve('DEPT', basis)
        except:
            raise Exception("Please provide a depth basis.")

        # Add meta from basis.
        setattr(l.well, 'STRT', basis[0])
        setattr(l.well, 'STOP', basis[-1])
        setattr(l.well, 'STEP', basis[1]-basis[0])

        # Add data entities.
        other = ''
        for k, d in self.data.items():

            try:
                # Treat as CURVE
                l.add_curve(k.upper(), d, unit=d.units, descr=d.description)
            except:
                # Treat as OTHER
                other += "{}\n".format(k.upper()) + d.to_csv()

        # Write OTHER, if any.
        if other:
            l.other = other

        return l

    def to_las(self, fname, basis=None):
        """
        Save a LAS file.
        """
        with open(fname, 'w') as f:
            self.to_lasio(basis=basis).write(f)

        return

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
        for field, (sect, code) in las_fields['data'].items():
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

    def plot_new(self, legend=None, tracks=None):
        """
        Even nicer plotting.
        """
        from matplotlib.gridspec import GridSpec

        # Set tracks to 'all' if it's None.
        tracks = tracks or list(self.data.keys())

        # Set up the figure.
        ntracks = len(tracks)
        fig = plt.figure(figsize=(2*ntracks, 12))
        gs = GridSpec(1, ntracks)

        for i, track in enumerate(tracks):
            ax = fig.add_subplot(gs[0, i])
            try:  # ...treating as a plottable objectself.
                self.data[track].plot(ax=ax, legend=legend)
            except TypeError:  # ...it's a list.
                for u in track:
                    self.data[u].plot(ax=ax, legend=legend)

        # Adjust the grid.
        gs.update(wspace=0)

        # Show only the outside spines.
        all_axes = fig.get_axes()
        for ax in all_axes:
            for sp in ax.spines.values():
                sp.set_visible(False)
            if ax.is_first_row():
                ax.spines['top'].set_visible(True)
            if ax.is_last_row():
                ax.spines['bottom'].set_visible(True)
            if ax.is_first_col():
                ax.spines['left'].set_visible(True)
            if ax.is_last_col():
                ax.spines['right'].set_visible(True)

        return None
