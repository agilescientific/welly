#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines wells.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import datetime

import matplotlib.pyplot as plt
import matplotlib as mpl
import lasio
import numpy as np

from . import utils
from .fields import las_fields
from .curve import Curve
from .header import Header
from .location import Location

###############################################
# This module is not used directly, but must
# be imported in order to register new scales.
from . import scales  # DO NOT DELETE
###############################################


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

        if getattr(self, 'data', None) is None:
            self.data = {}

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
        """
        Property. Simply a shortcut to the UWI from the header, or the
        empty string if there isn't one.
        """
        return getattr(self.header, 'uwi', None) or ''

    @classmethod
    def from_lasio(cls, l, remap=None, funcs=None):
        """
        Constructor. If you already have the lasio object, then this makes a
        well object from it.

        Args:
            l (lasio object): a lasio object.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            well. The well object.
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
        Constructor. Essentially just wraps ``from_lasio()``, but is more
        convenient for most purposes.

        Args:
            fname (str): The path of the LAS file.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            well. The well object.
        """
        l = lasio.read(fname)

        # Pass to other constructor.
        return cls.from_lasio(l, remap=remap, funcs=funcs)

    def to_lasio(self, basis=None, keys=None):
        """
        Makes a lasio object from the current well.

        Args:
            basis (ndarray): Optional. The basis to export the curves in. If
                you don't specify one, it will survey all the curves with
                ``survey_basis()``.
            keys (list): List of strings: the keys of the data items to
                include, if not all of them. You can have nested lists, such
                as you might use for ``tracks`` in ``well.plot()``.

        Returns:
            lasio. The lasio object.
        """

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
            basis = self.survey_basis(keys=keys)
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
        keys = utils.flatten_list(keys) or list(self.data.keys())
        for k in keys:
            d = self.data[k]
            if getattr(d, 'null', None) is not None:
                d[np.isnan(d)] = d.null
            try:
                new_data = np.copy(d.to_basis_like(basis))
            except:
                raise WellError("basis shift failed")
            try:
                descr = d.description
                l.add_curve(k.upper(), new_data, unit=d.units, descr=descr)
            except:
                try:
                    # Treat as OTHER
                    other += "{}\n".format(k.upper()) + d.to_csv()
                except:
                    pass

        # Write OTHER, if any.
        if other:
            l.other = other

        return l

    def to_las(self, fname, basis=None, keys=None):
        """
        Writes the current well instance as a LAS file. Essentially just wraps
        ``to_lasio()``, but is more convenient for most purposes.

        Args:
            fname (str): The path of the LAS file to create.
            basis (ndarray): Optional. The basis to export the curves in. If
                you don't specify one, it will survey all the curves with
                ``survey_basis()``.
            keys (list): List of strings: the keys of the data items to
                include, if not all of them. You can have nested lists, such
                as you might use for ``tracks`` in ``well.plot()``.

        Returns:
            None. Writes the file as a side-effect.
        """
        with open(fname, 'w') as f:
            self.to_lasio(basis=basis, keys=keys).write(f)

        return

    def add_curves_from_las(self, fname, remap=None, funcs=None):
        """
        Given a LAS file, add curves from it to the current well instance.
        Essentially just wraps ``add_curves_from_lasio()``.

        Args:
            fname (str): The path of the LAS file to read curves from.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            None. Works in place.
        """
        l = lasio.read(fname)

        # Pass to other constructor.
        return self.add_curves_from_lasio(l, remap=remap, funcs=funcs)

    def add_curves_from_lasio(self, l, remap=None, funcs=None):
        """
        Given a LAS file, add curves from it to the current well instance.
        Essentially just wraps ``add_curves_from_lasio()``.

        Args:
            fname (str): The path of the LAS file to read curves from.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            None. Works in place.
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

        # This will clobber anything with the same key!
        self.data.update(curves)

        return None

    def _plot_depth_track(self, ax, md, kind='MD'):
        """
        Private function. Depth track plotting.

        Args:
            ax (ax): A matplotlib axis.
            md (ndarray): The measured depths of the track.
            kind (str): The kind of track to plot.

        Returns:
            ax.
        """
        if kind == 'MD':
            ax.set_yscale('bounded', vmin=md.min(), vmax=md.max())
            # ax.set_ylim([md.max(), md.min()])
        elif kind == 'TVD':
            tvd = self.location.md2tvd(md)
            ax.set_yscale('piecewise', x=tvd, y=md)
            # ax.set_ylim([tvd.max(), tvd.min()])
        else:
            raise Exception("Kind must be MD or TVD")

        for sp in ax.spines.values():
            sp.set_color('gray')

        if ax.is_first_col():
            pad = -10
            ax.spines['left'].set_color('none')
            ax.yaxis.set_ticks_position('right')
            for label in ax.get_yticklabels():
                label.set_horizontalalignment('right')
        elif ax.is_last_col():
            pad = -10
            ax.spines['right'].set_color('none')
            ax.yaxis.set_ticks_position('left')
            for label in ax.get_yticklabels():
                label.set_horizontalalignment('left')
        else:
            pad = -30
            for label in ax.get_yticklabels():
                label.set_horizontalalignment('center')

        ax.tick_params(axis='y', colors='gray', labelsize=12, pad=pad)
        ax.set_xticks([])

        ax.set(xticks=[])
        ax.depth_track = True

        return ax

    def plot(self,
             legend=None,
             tracks=None,
             track_titles=None,
             basis=None,
             return_fig=False):
        """
        Plot multiple tracks.

        Args:
            legend (striplog.legend): A legend instance.
            tracks (list): A list of strings and/or lists of strings. The
                tracks you want to plot from ``data``. Optional, but you will
                usually want to give it.
            track_titles (list): Optional. A list of strings and/or lists of
                strings. The names to give the tracks, if you don't want welly
                to guess.
            basis (ndarray): Optional. The basis of the plot, if you don't
                want welly to guess (probably the best idea).
            return_fig (bool): Whether to return the matplotlig figure. Default
                False.

        Returns:
            None. The plot is a side-effect.
        """
        # These will be treated differently.
        depth_tracks = ['MD', 'TVD']

        # Set tracks to 'all' if it's None.
        tracks = tracks or list(self.data.keys())
        track_titles = track_titles or tracks

        # Figure out limits
        if basis is None:
            basis = self.survey_basis(keys=tracks)
        upper, lower = basis[0], basis[-1]

        # Figure out widths because we can't us gs.update() for that.
        widths = [0.4 if t in depth_tracks else 1.0 for t in tracks]

        # Set up the figure.
        ntracks = len(tracks)
        fig = plt.figure(figsize=(2*ntracks, 12), facecolor='w')
        fig.suptitle(self.header.name, size=16, zorder=100,
                     bbox=dict(facecolor='w', alpha=1.0, ec='none'))
        gs = mpl.gridspec.GridSpec(1, ntracks, width_ratios=widths)

        # Plot first axis.
        kwargs = {}
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.depth_track = False
        track = tracks[0]
        if '.' in track:
            track, kwargs['field'] = track.split('.')
        if track in depth_tracks:
            ax0 = self._plot_depth_track(ax=ax0, md=basis, kind=track)
        else:
            try:  # ...treating as a plottable object.
                ax0 = self.data[track].plot(ax=ax0, legend=legend, **kwargs)
            except TypeError:  # ...it's a list.
                for t in track:
                    ax0 = self.data[t].plot(ax=ax0, legend=legend, **kwargs)
        tx = ax0.get_xticks()
        ax0.set_xticks(tx[1:-1])
        ax0.set_title(track_titles[0])

        # Plot remaining axes.
        for i, track in enumerate(tracks[1:]):
            kwargs = {}
            ax = fig.add_subplot(gs[0, i+1])
            ax.depth_track = False
            ax.set_title(track_titles[i+1])
            if track in depth_tracks:
                ax = self._plot_depth_track(ax=ax, md=basis, kind=track)
                continue
            if '.' in track:
                track, kwargs['field'] = track.split('.')
            plt.setp(ax.get_yticklabels(), visible=False)
            try:  # ...treating as a plottable objectself.
                ax = self.data[track].plot(ax=ax, legend=legend, **kwargs)
                ax.text(0.5, 1.00, ax.get_title(), color='k', fontsize=12,
                        transform=ax.transAxes, ha='center', va='bottom')
            except TypeError:  # ...it's a list.
                for j, t in enumerate(track):
                    if '.' in t:
                        track, kwargs['field'] = track.split('.')
                    try:
                        ax = self.data[t].plot(ax=ax, legend=legend, **kwargs)
                        ax.text(0.5, 1.0 + 0.02 * j, ax.get_title(),
                                color=legend.get_decor(self.data[t]).colour,
                                transform=ax.transAxes,
                                ha='center', va='bottom', fontsize=12)
                    except KeyError:
                        continue

            tx = ax.get_xticks()
            ax.set_xticks(tx[1:-1])
            ax.title.set_visible(False)  # turn off "Title" because we're using text

        # Set sharing.
        axes = fig.get_axes()
        utils.sharey(axes)
        axes[0].set_ylim([lower, upper])

        # Adjust the grid.
        gs.update(wspace=0)

        # Adjust spines and ticks for non-depth tracks.
        for ax in axes:
            if ax.depth_track:
                pass
            if not ax.depth_track:
                ax.set(yticks=[])
                ax.autoscale(False)
                ax.yaxis.set_ticks_position('none')
                ax.spines['top'].set_visible(True)
                ax.spines['bottom'].set_visible(True)
                for sp in ax.spines.values():
                    sp.set_color('gray')

        if return_fig:
            return fig
        else:
            return None

    def survey_basis(self, keys=None):
        """
        Look at the basis of all the curves in the ``well.data`` and return a
        basis with the minimum start, maximum depth, and minimum step.

        Args:
            keys (list): List of strings: the keys of the data items to
                survey, if not all of them.

        Returns:
            ndarray. The 'most complete common basis'.
        """
        keys = utils.flatten_list(keys)
        starts, stops, steps = [], [], []
        for k, d in self.data.items():
            if (keys is not None) and (k not in keys):
                continue
            try:
                starts.append(d.basis[0])
                stops.append(d.basis[-1])
                steps.append(d.basis[1] - d.basis[0])
            except:
                pass
        if starts and stops and steps:
            return np.arange(min(starts), max(stops)+1e-9, min(steps))
        else:
            return None
