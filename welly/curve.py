#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines log curves.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np
import matplotlib.pyplot as plt

from . import utils


class CurveError(Exception):
    """
    Generic error class.
    """
    pass


class Curve(np.ndarray):

    def __new__(cls, data, params=None):
        obj = np.asarray(data).view(cls).copy()

        for k, v in params.items():
            setattr(obj, k, v)

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

        if obj.size == 1:
            return float(obj)

        basis = getattr(obj, 'basis', None)
        if basis is None:
            self.start = getattr(obj, 'start', 0)
            self.step = getattr(obj, 'step', 0.1524)
        else:
            self.start = basis[0]
            self.step = basis[1] - basis[0]

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
                         start=None,
                         step=0.1524,
                         run=-1,
                         null=-999.25,
                         service_company=None,
                         date=None):
        """
        Provide a lasio curve object and a depth basis.
        """
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
        Apply a function to the curve.

        Args:
            Function.
            kwargs. Arguments for the function.

        Returns:
            Curve.
        """
        params = self.__dict__.copy()
        data = function(self, **kwargs)
        params['units'] = ''  # These will often break otherwise.
        return Curve(data, params)

    def plot(self, ax=None, legend=None, **kwargs):
        """
        Plot a curve.
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

        ax.set_title(self.mnemonic)
        ax.set_xlabel(self.units)
        ax.plot(self, self.basis, c=c, lw=lw, ls=ls)

        ax.set_ylim([self.stop, self.start])
        ax.grid('on', color='k',  alpha=0.2, lw=0.25, linestyle='-')

        if return_ax:
            return ax
        else:
            return None

    def to_basis_like(self, basis):
        """
        Make a new basis, given an existing one. Wraps ``to_basis()``.

        Pass in a curve or the basis of a curve.
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
        Reset the start, stop, and/or step.

        Needs to handle extrapolating / padding
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

        return Curve(data, params)

    # DEPRECATE WHEN WE KNOW WHAT NEW_BASIS DOES
    def segment(self, d):
        """
        Returns a segment of the log between the depths specified.

        Args:
            d (tuple): A tuple of floats giving top and base of interval.

        Returns:
            Curve. The new curve segment.
        """
        top = self._read_at(d[0], index=True) + 1  # b/c returns index before
        base = self._read_at(d[1], index=True)

        data = self[top:base]
        params = self.__dict__.copy()
        params['start'] = d[0]
        return Curve(data, params)

    def _read_at(self, d,
                 interpolation='linear',
                 index=False,
                 return_basis=False):
        """
        Private function. Implements read_at() for a single depth.

        Args:
            d (float or array-like)
            interpolation (str)
            index(bool)
            return_basis (bool)

        Returns:
            float or ndarray.
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

    def block(self, cutoffs=None, values=None, n_bins=0, right=False, function=None):
        """
        Block a log based on number of bins, or on cutoffs.

        Args:
            cutoffs (array)
            values (array)
            n_bins (int)
            right (bool)
            function (function)

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
            return Curve(data, params)

        data = data.astype(float)

        # Set the function for reducing.
        f = function or utils.null

        # Find the tops of the 'zones'.
        tops, vals = utils.find_edges(data)

        # End of array trick... adding this should remove the
        # need for the marked lines below. But it doesn't.
        #np.append(tops, None)
        #np.append(vals, None)

        if values is None:
            # Transform each segment in turn, then deal with the last segment.
            for top, base in zip(tops[:-1], tops[1:]):
                data[top:base] = f(np.copy(self[top:base]))
            data[base:] = f(np.copy(self[base:]))  # See above
        else:
            for top, base, val in zip(tops[:-1], tops[1:], vals[:-1]):
                data[top:base] = values[int(val)]
            data[base:] = values[int(vals[-1])]  # See above

        return Curve(data, params)
