#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines log curves.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

from . import utils


class CurveError(Exception):
    """
    Generic error class.
    """
    pass


class Curve(np.ndarray):
    """
    A fancy ndarray. Gives some utility functions, plotting, etc, for curve
    data.
    """
    def __new__(cls, data, basis=None, params=None):
        """
        I am just following the numpy guide for subclassing ndarray...
        """
        obj = np.asarray(data).view(cls).copy()

        params = params or {}

        for k, v in params.items():
            setattr(obj, k, v)

        if basis is not None:
            setattr(obj, 'start', basis[0])
            setattr(obj, 'step', basis[1]-basis[0])

        return obj

    def __array_finalize__(self, obj):
        """
        I am just following the numpy guide for subclassing ndarray...
        """
        if obj is None:
            return

        if obj.size == 1:
            return float(obj)

        self.start = getattr(obj, 'start', 0)
        self.step = getattr(obj, 'step', 0)
        self.mnemonic = getattr(obj, 'mnemonic', None)
        self.units = getattr(obj, 'units', None)
        self.run = getattr(obj, 'run', 0)
        self.null = getattr(obj, 'null', -999.25)
        self.service_company = getattr(obj, 'service_company', None)
        self.date = getattr(obj, 'date', None)
        self.code = getattr(obj, 'code', None)

    def _repr_html_(self):
        """
        Jupyter Notebook magic repr function.
        """
        if self.size < 10:
            return np.ndarray.__repr__(self)
        attribs = self.__dict__.copy()
        row1 = '<tr><th style="text-align:center;" colspan="2">{} [{{}}]</th></tr>'
        rows = row1.format(attribs.pop('mnemonic'))
        rows = rows.format(attribs.pop('units', '&ndash;'))
        row2 = '<tr><td style="text-align:center;" colspan="2">{:.4f} : {:.4f} : {:.4f}</td></tr>'
        rows += row2.format(attribs.pop('start'), self.stop, attribs.pop('step'))
        s = '<tr><td><strong>{k}</strong></td><td>{v}</td></tr>'
        for k, v in attribs.items():
            rows += s.format(k=k, v=v)
        s = '<tr><th style="border-top: 2px solid #000;">Depth</th><th style="border-top: 2px solid #000;">Value</th></tr>'
        rows += s.format(self.start, self[0])
        s = '<tr><td>{:.4f}</td><td>{:.4f}</td></tr>'
        for depth, value in zip(self.basis[:3], self[:3]):
            rows += s.format(depth, value)
        rows += '<tr><td>⋮</td><td>⋮</td></tr>'
        for depth, value in zip(self.basis[-3:], self[-3:]):
            rows += s.format(depth, value)
        html = '<table>{}</table>'.format(rows)
        return html

    @property
    def stop(self):
        return self.start + self.shape[0] * self.step

    @property
    def basis(self):
        precision_adj = self.step / 100
        return np.arange(self.start, self.stop - precision_adj, self.step)

    @classmethod
    def from_lasio_curve(cls, curve,
                         basis=None,
                         start=None,
                         step=0.1524,
                         run=-1,
                         null=-999.25,
                         service_company=None,
                         date=None):
        """
        Makes a curve object from a lasio curve object and either a depth
        basis or start and step information.

        Args:
            curve (ndarray)
            basis (ndarray)
            start (float)
            step (float): default: 0.1524
            run (int): default: -1
            null (float): default: -999.25
            service_company (str): Optional.
            data (str): Optional.

        Returns:
            Curve. An instance of the class.
        """
        if start is None:
            if basis is not None:
                start = basis[0]
                step = basis[1] - basis[0]
            else:
                raise CurveError("You must provide a basis or a start depth.")

        params = {}
        params['mnemonic'] = curve.mnemonic
        params['description'] = curve.descr
        params['start'] = start
        params['step'] = step
        params['units'] = curve.unit
        params['run'] = run
        params['null'] = null
        params['service_company'] = service_company
        params['date'] = date
        params['code'] = curve.API_code

        return cls(curve.data, params=params)

    def apply(self, function, **kwargs):
        """
        Apply a function to the curve. Pretty sure we don't need this.

        Args:
            function (function): A functon to apply.
            kwargs. Arguments for the function.

        Returns:
            Curve.
        """
        params = self.__dict__.copy()
        data = function(self, **kwargs)
        params['units'] = ''  # These will often break otherwise.
        return Curve(data, params=params)

    def plot_2d(self, ax=None,
                width=None,
                aspect=60,
                cmap=None,
                ticks=(1, 10),
                return_fig=False):
        """
        Plot a 2D curve.

        Args:
            ax (ax): A matplotlib axis.
            width (int): The width of the image.
            aspect (int): The aspect ratio (not quantitative at all).
            cmap (str): The colourmap to use.
            ticks (tuple): The tick interval on the y-axis.
            return_fig (bool): whether to return the matplotlib figure.
                Default False.

        Returns:
            ax. If you passed in an ax, otherwise None.
        """
        if ax is None:
            fig = plt.figure(figsize=(2, 10))
            ax = fig.add_subplot(111)
            return_ax = False
        else:
            return_ax = True

        cmap = cmap or 'viridis'
        default = int(self.shape[0] / aspect)
        if self.ndim == 1:
            a = np.expand_dims(self, axis=1)
            a = np.repeat(a, width or default, axis=1)
        elif self.ndim == 2:
            a = self[:, :width]
        elif self.ndim == 3:
            if 2 < self.shape[-1] < 5:
                # Interpret as RGB or RGBA.
                a = utils.normalize(np.copy(self))
                cmap = None  # Actually doesn't matter.
            else:
                # Take first slice.
                a = self[:, :width, 0]
        else:
            raise NotImplementedError("Can only handle up to 3 dimensions.")

        # At this point, a is either a 2D array, or a 2D (rgb) array.
        extent = [0, width or default, self.stop, self.start]
        _ = ax.imshow(a, cmap=cmap, extent=extent)
        ax.set_xticks([])

        # Rely on interval order.
        lower, upper = self.stop, self.start
        rng = abs(upper - lower)

        ax.set_ylim([lower, upper])

        # Make sure ticks is a tuple.
        try:
            ticks = tuple(ticks)
        except TypeError:
            ticks = (1, ticks)

        # Avoid MAXTICKS error.
        while rng/ticks[0] > 250:
            mi, ma = 10*ticks[0], ticks[1]
            if ma <= mi:
                ma = 10 * mi
            ticks = (mi, ma)

        # Carry on plotting...
        minorLocator = mpl.ticker.MultipleLocator(ticks[0])
        ax.yaxis.set_minor_locator(minorLocator)

        majorLocator = mpl.ticker.MultipleLocator(ticks[1])
        majorFormatter = mpl.ticker.FormatStrFormatter('%d')
        ax.yaxis.set_major_locator(majorLocator)
        ax.yaxis.set_major_formatter(majorFormatter)

        ax.yaxis.set_ticks_position('left')
        ax.get_yaxis().set_tick_params(which='both', direction='out')

        if return_ax:
            return ax
        elif return_fig:
            return fig
        else:
            return None

    def plot(self, ax=None, legend=None, return_fig=False, **kwargs):
        """
        Plot a curve.

        Args:
            ax (ax): A matplotlib axis.
            legend (striplog.legend): A legend. Optional.
            return_fig (bool): whether to return the matplotlib figure.
                Default False.
            kwargs: Arguments for ``ax.set()``

        Returns:
            ax. If you passed in an ax, otherwise None.
        """
        if ax is None:
            fig = plt.figure(figsize=(2, 10))
            ax = fig.add_subplot(111)
            return_ax = False
        else:
            return_ax = True

        c = None
        d = None
        if legend is not None:
            try:
                d = legend.get_decor(self)
                c = d.colour
            except:
                pass

        if d is not None:
            # Then attempt to get parameters from decor.
            axkwargs = {}

            xticks = getattr(d, 'xticks', None)
            if xticks is not None:
                axkwargs['xticks'] = list(map(float, xticks.split(',')))

            xscale = getattr(d, 'xscale', None)
            if xscale is not None:
                axkwargs['xscale'] = xscale

            ax.set(**axkwargs)

        lw = getattr(d, 'lineweight', None) or getattr(d, 'lw', 1)
        ls = getattr(d, 'linestyle', None) or getattr(d, 'ls', '-')

        ax.plot(self, self.basis, c=c, lw=lw, ls=ls)
        ax.set_title(self.mnemonic)  # no longer needed
        ax.set_xlabel(self.units)

        if False:  # labeltop of axes?
            ax.xaxis.tick_top()

        if True:  # rotate x-tick labels
            labels = ax.get_xticklabels()
            for label in labels:
                label.set_rotation(90)

        ax.set_ylim([self.stop, self.start])
        ax.grid('on', color='k', alpha=0.2, lw=0.25, linestyle='-')

        if return_ax:
            return ax
        elif return_fig:
            return fig
        else:
            return None

    def extrapolate(self):
        return utils.extrapolate(self)

    def to_basis_like(self, basis):
        """
        Make a new curve in a new basis, given an existing one. Wraps
        ``to_basis()``.

        Pass in a curve or the basis of a curve.

        Args:
            basis (ndarray): A basis, but can also be a Curve instance.

        Returns:
            Curve. The current instance in the new basis.
        """
        try:  # To treat as a curve.
            curve = basis
            basis = curve.basis
            undefined = curve.null
        except:
            undefined = None
        start = basis[0]
        step = basis[1] - basis[0]
        stop = basis[-1]

        return self.to_basis(start, stop, step, undefined=undefined)

    def to_basis(self, start=None, stop=None, step=None, undefined=None):
        """
        Make a new curve in a new basis, given a new start, step, and stop.
        You only need to set the parameters you want to change. If the new
        extents go beyond the current extents, the curve is padded with the
        ``undefined`` parameter.

        Args:
            start (float)
            stop (float)
            step (float)
            undefined (float)

        Returns:
            Curve. The current instance in the new basis.
        """
        new_start = start or self.start
        new_step = step or self.step
        new_stop = stop or self.stop

        if undefined is None:
            undefined = np.nan
        undefined = {'left': undefined,
                     'right': undefined
                     }

        new_adj_stop = new_stop + new_step/100  # To guarantee inclusion.
        new_basis = np.arange(new_start, new_adj_stop, new_step)
        data = np.interp(new_basis, self.basis, self, **undefined)

        params = self.__dict__.copy()
        params['step'] = float(new_step)
        params['start'] = float(new_start)

        return Curve(data, params=params)

    def _read_at(self, d,
                 interpolation='linear',
                 index=False,
                 return_basis=False):
        """
        Private function. Implements read_at() for a single depth.

        Args:
            d (float)
            interpolation (str)
            index(bool)
            return_basis (bool)

        Returns:
            float
        """
        method = {'linear': utils.linear,
                  'none': None}

        i, d = utils.find_previous(self.basis,
                                   d,
                                   index=True,
                                   return_distance=True)

        if index:
            return i
        else:
            return method[interpolation](self[i], self[i+1], d)

    def read_at(self, d, **kwargs):
        """
        Read the log at a specific depth or an array of depths.

        Args:
            d (float or array-like)
            interpolation (str)
            index(bool)
            return_basis (bool)

        Returns:
            float or ndarray.
        """
        try:
            return np.array([self._read_at(depth, **kwargs) for depth in d])
        except:
            return self._read_at(d, **kwargs)

    def block(self,
              cutoffs=None,
              values=None,
              n_bins=0,
              right=False,
              function=None):
        """
        Block a log based on number of bins, or on cutoffs.

        Args:
            cutoffs (array)
            values (array): the values to map to. Defaults to [0, 1, 2,...]
            n_bins (int)
            right (bool)
            function (function): transform the log if you want.

        Returns:
            Curve.
        """
        # We'll return a copy.
        params = self.__dict__.copy()

        if (values is not None) and (cutoffs is None):
            cutoffs = values[1:]

        if (cutoffs is None) and (n_bins == 0):
            cutoffs = np.mean(self)

        if (n_bins != 0) and (cutoffs is None):
            mi, ma = np.amin(self), np.amax(self)
            cutoffs = np.linspace(mi, ma, n_bins+1)
            cutoffs = cutoffs[:-1]

        try:  # To use cutoff as a list.
            data = np.digitize(self, cutoffs, right)
        except ValueError:  # It's just a number.
            data = np.digitize(self, [cutoffs], right)

        if (function is None) and (values is None):
            return Curve(data, params=params)

        data = data.astype(float)

        # Set the function for reducing.
        f = function or utils.null

        # Find the tops of the 'zones'.
        tops, vals = utils.find_edges(data)

        # End of array trick... adding this should remove the
        # need for the marked lines below. But it doesn't.
        # np.append(tops, None)
        # np.append(vals, None)

        if values is None:
            # Transform each segment in turn, then deal with the last segment.
            for top, base in zip(tops[:-1], tops[1:]):
                data[top:base] = f(np.copy(self[top:base]))
            data[base:] = f(np.copy(self[base:]))  # See above
        else:
            for top, base, val in zip(tops[:-1], tops[1:], vals[:-1]):
                data[top:base] = values[int(val)]
            data[base:] = values[int(vals[-1])]  # See above

        return Curve(data, params=params)

    def _rolling_window(self, window):
        """
        Private function. Smoother for the despiker to work on.

        Args:
            window (int): the window length.
        """
        # Force odd.
        if window % 2 == 0:
            window += 1
        shape = self.shape[:-1] + (self.shape[-1] - window + 1, window)
        strides = self.strides + (self.strides[-1],)
        rolled = np.lib.stride_tricks.as_strided(self,
                                                 shape=shape,
                                                 strides=strides)
        rolled = np.median(rolled, -1)
        rolled = np.pad(rolled, window//2, mode='edge')

        return rolled

    def despike(self, window=33, z=2):
        """
        Args:
            window (int): window length in samples. Default 33 (or 5 m for
                most curves).
            z (float): Z score

        Returns:
            Curve.
        """
        z *= np.std(self)  # Transform to curve's units
        curve_sm = self._rolling_window(window)
        spikes = np.where(self - curve_sm > z)[0]
        spukes = np.where(curve_sm - self > z)[0]
        out = np.copy(self)
        params = self.__dict__.copy()
        out[spikes] = curve_sm[spikes] + z
        out[spukes] = curve_sm[spukes] - z
        return Curve(out, params=params)
