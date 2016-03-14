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
import numpy as np

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
        rows = row1.format(getattr(self.header, 'name', ''))
        rows = rows.format(getattr(self.header, 'uwi', ''))
        s = '<tr><td><strong>{k}</strong></td><td>{v}</td></tr>'

        if getattr(self, 'location', None) is not None:
            for k, v in self.location.__dict__.items():
                if k in ['deviation', 'position']:
                    continue
                rows += s.format(k=k, v=v)

        if getattr(self, 'data', None) is not None:
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

    def survey_basis(self):
        starts, stops, steps = [], [], []
        for c in self.data:
            try:
                starts.append(c.basis[0])
                stops.append(c.basis[-1])
                steps.append(c.basis[1] - c.basis[0])
            except:
                pass
        if starts and stops and steps:
            return np.arange(min(starts), max(stops)+1e-9, min(steps))
        else:
            return None

    @classmethod
    def from_las(cls, fname, remap=None, funcs=None):
        """
        Wraps lasio.
        """
        l = lasio.read(fname)

        # Pass to other constructor.
        return cls.from_lasio(l, remap=remap, funcs=funcs)

    def to_lasio(self, basis=None, keys=None):
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
        if basis is None:
            basis = self.survey_basis()

        try:
            l.add_curve('DEPT', basis)
        except:
            raise Exception("Please provide a depth basis.")

        # Add meta from basis.
        setattr(l.well, 'STRT', basis[0])
        setattr(l.well, 'STOP', basis[-1])
        setattr(l.well, 'STEP', basis[1]-basis[0])

        # Add data entities.
        other = ''
        keys = utils.flatten_list(keys) or self.data.keys()
        for k, d in self.data.items():
            if k not in keys:
                continue
            try:
                # Continue treating as CURVE.
                l.add_curve(k.upper(), d.to_basis_like(basis), unit=d.units, descr=d.description)
            except:
                # Treat as OTHER
                other += "{}\n".format(k.upper()) + d.to_csv()

        # Write OTHER, if any.
        if other:
            l.other = other

        return l

    def to_las(self, fname, basis=None, keys=None):
        """
        Save a LAS file.
        """
        with open(fname, 'w') as f:
            self.to_lasio(basis=basis, keys=keys).write(f)

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

        kwargs = {}
        for i, track in enumerate(tracks):
            if '.' in track:
                track, kwargs['field'] = track.split('.')
            if ntracks == 1:
                axarr = [axarr]
            try:  # ...treating as a plottable objectself.
                self.data[track].plot(ax=axarr[i], legend=legend)
            except TypeError:  # ...it's a list.
                for j, u in enumerate(track):
                    if j == 0:
                        thisax = axarr[i]
                    else:
                        thisax = thisax.twiny()
                    try:
                        self.data[u].plot(ax=thisax, legend=legend, **kwargs)
                    except KeyError:
                        continue

        return None

    def plot_new(self, legend=None, tracks=None, track_titles=None):
        """
        Even nicer plotting.

        tracks (dict)
        """
        from matplotlib.gridspec import GridSpec

        # Set tracks to 'all' if it's None.
        tracks = tracks or self.data.keys()
        track_titles = track_titles or tracks

        # Set up the figure.
        ntracks = len(tracks)
        fig = plt.figure(figsize=(2*ntracks, 12))
        gs = GridSpec(1, ntracks)

        # Plot first axis.
        ax0 = fig.add_subplot(gs[0, 0])
        try:  # ...treating as a plottable objectself.
            self.data[tracks[0]].plot(ax=ax0, legend=legend)
        except TypeError:  # ...it's a list.
            for t in tracks[0]:
                self.data[t].plot(ax=ax0, legend=legend)
        ax0.set_title(track_titles[0])

        # Plot special depth axis.
        # http://stackoverflow.com/questions/7733693/matplotlib-overlay-plots-with-different-scales/7734614
        # daxes = [ax0, ax0.twinx()]
        # fig.subplots_adjust(left=0.25)
        # daxes[-1].spines['left'].set_position(('axes', 0.))

        # Try to put depth scale on right too.
        # ax00 = ax0.twinx()
        # ax00.yaxis.set_label_position("right")

        # Plot remaining axes.
        for i, track in enumerate(tracks[1:]):
            ax = fig.add_subplot(gs[0, i+1], sharey=ax0)
            plt.setp(ax.get_yticklabels(), visible=False)
            try:  # ...treating as a plottable objectself.
                self.data[track].plot(ax=ax, legend=legend)
            except TypeError:  # ...it's a list.
                for t in track:
                    try:
                        self.data[t].plot(ax=ax, legend=legend)
                    except KeyError:
                        continue
            ax.set_title(track_titles[i+1])

        # Title
        fig.suptitle(self.header.name, size=16)

        # Adjust the grid.
        gs.update(wspace=0)

        # Show only the outside spines.
        all_axes = fig.get_axes()
        for ax in all_axes:
            # Turn off y ticks.
            ax.yaxis.set_ticks_position('none')

            # Turn off all spines.
            for sp in ax.spines.values():
                sp.set_visible(False)

            # Turn back on for left-hand sides.
            ax.spines['left'].set_visible(True)

            # Turn some others back on.
            if ax.is_first_row():
                ax.spines['top'].set_visible(True)
            if ax.is_last_row():
                ax.spines['bottom'].set_visible(True)
            # if ax.is_first_col():
            #     ax.spines['left'].set_visible(True)
            if ax.is_last_col():
                ax.spines['right'].set_visible(True)

        return None
