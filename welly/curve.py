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
        if obj is None: return

        self.start = getattr(obj, 'start', 0)
        self.step = getattr(obj, 'step', 0.1524)
        self.mnemonic = getattr(obj, 'mnemonic', None)
        self.units = getattr(obj, 'units', None)

    @property
    def stop(self):
        return self.start + self.shape[0] * self.step

    @property
    def basis(self):
        precision_adj = self.step / 100
        return np.arange(self.start, self.stop - precision_adj, self.step)

    @classmethod
    def from_lasio_curve(cls, curve, start=None, step=0.1524, run=-1, null=-999.25):
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

    def plot(self, **kwargs):
        """
        Plot a curve.
        """
        fig = plt.figure(figsize=(2, 10))
        ax = fig.add_subplot(111)
        ax.plot(self, self.basis, **kwargs)
        ax.set_title(self.mnemonic)
        ax.set_ylim([self.stop, self.start])
        ax.set_xlabel(self.units)
        ax.grid()
        return

    def segment(self, d):
        """
        Returns a segment of the log between the depths specified.

        Args:
            d (tuple): A tuple of floats giving top and base of interval.

        Returns:
            Curve. The new curve segment.
        """
        top = self._read_at(d[0], index=True)
        base = self._read_at(d[1], index=True)

        data = self[top:base]
        params = self.__dict__.copy()  # copy attributes from main curve
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

        if values is None:
            # Transform each segment in turn, then deal with the last segment.
            for top, base in zip(tops[:-1], tops[1:]):
                data[top:base] = f(np.copy(self[top:base]))
            data[base:] = f(np.copy(self[base:]))
        else:
            for top, base, val in zip(tops[:-1], tops[1:], vals[:-1]):
                data[top:base] = values[int(val)]
            data[base:] = values[int(vals[-1])]

        return Curve(data, params)

    def mean(self):
        """
        Could have all sorts of helpful transforms etc.
        """
        try:
            return np.mean(np.copy(self))
        except:
            raise CurveError("You can't do that.")
