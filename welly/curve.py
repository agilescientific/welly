#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines log curves.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import operator
from functools import partial

import numpy as np
import matplotlib.pyplot as plt

from . import utils


class CurveError(Exception):
    """
    Generic error class.
    """
    pass


class Curve(object):
    """
    Class for log curves.
    """
    def __init__(self, params):
        """
        Args:
            params (dict or lasio.Curve)
            basis (array-like): An array representing depth.
        """
        if params['basis'] is None:
            raise CurveError('you must provide a depth basis.')

        # Take care of the most important things.
        self.basis = params.pop('basis')
        self.data = params.pop('data')

        # Churn through remaining params.
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

    def __str__(self):
        """
        What to return for ``print(instance)``.
        """
        if self.units:
            s = "{} [{}]: {} samples"
            return s.format(self.mnemonic, self.units, self.data.size)
        else:
            s = "{}: {} samples"
            return s.format(self.mnemonic, self.data.size)

    def __pow__(self, exponent):
        return self.apply(lambda x: pow(x, exponent))

    @property
    def start(self):
        return self.basis[0]

    @property
    def stop(self):
        return self.basis[-1]

    @property
    def step(self):
        """
        If all steps are equal, returns the step.

        If not, returns None.
        """
        first = self.basis[1] - self.basis[0]
        if np.all(self.basis == first):
            return self.basis[1] - self.basis[0]
        else:
            return None

    @step.setter
    def step(self, value):
        """
        Sets a new (regular) step, retaining the existing start.
        """
        new_basis = np.arange(self.start, self.stop, value)
        self.data = np.interp(new_basis, self.basis, self.data)
        self.basis = new_basis

    @classmethod
    def from_lasio_curve(cls, curve, basis=None, run=-1, null=-999.25):
        """
        Provide a lasio curve object and a depth basis.
        """
        if basis is None:
            raise CurveError('you must provide a depth basis.')

        params = {}
        params['basis'] = basis
        params['mnemonic'] = curve.mnemonic
        params['description'] = curve.descr
        params['units'] = curve.unit
        params['data'] = curve.data
        params['run'] = run
        params['null'] = null

        return cls(params)

    def plot(self, **kwargs):
        """
        Plot a curve.
        """
        fig = plt.figure(figsize=(2, 10))
        ax = fig.add_subplot(111)
        ax.plot(self.data, self.basis, **kwargs)
        ax.set_title(self.mnemonic)
        ax.set_ylim([self.stop, self.start])
        ax.set_xlabel(self.units)
        ax.grid()
        return

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
        params['data'] = function(self.data, **kwargs)
        params['units'] = ''
        return Curve(params)

    def segment(self, d):
        """
        Returns a segment of the log between the depths specified.

        Args:
            d (tuple): A tuple of floats giving top and base of interval.

        Returns:
            Curve. The new curve segment.
        """
        top_idx = utils.find_previous(self.basis, d[0], index=True)
        base_idx = utils.find_previous(self.basis, d[1], index=True)
        params = self.__dict__.copy()  # copy attributes from main curve
        params['data'] = self.data[top_idx:base_idx]
        params['basis'] = self.basis[top_idx:base_idx]
        return Curve(params)

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

        value = method[interpolation](self.data[i], self.data[i+1], d)
        return value

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
            cutoffs = np.mean(self.data)

        if (n_bins != 0) and (cutoffs is None):
            mi, ma = np.amin(self.data), np.amax(self.data)
            cutoffs = np.linspace(mi, ma, n_bins+1)
            cutoffs = cutoffs[:-1]

        try:  # To use cutoff as a list.
            params['data'] = np.digitize(self.data, cutoffs, right)
        except ValueError:  # It's just a number.
            params['data'] = np.digitize(self.data, [cutoffs], right)

        if (function is None) and (values is None):
            return Curve(params)

        params['data'] = params['data'].astype(float)

        # Set the function for reducing.
        f = function or utils.null

        # Find the tops of the 'zones'.
        tops, vals = utils.find_edges(params['data'])

        if values is None:
            # Transform each segment in turn, then deal with the last segment.
            for top, base in zip(tops[:-1], tops[1:]):
                params['data'][top:base] = f(self.data[top:base])
            params['data'][base:] = f(self.data[base:])
        else:
            for top, base, val in zip(tops[:-1], tops[1:], vals[:-1]):
                params['data'][top:base] = values[int(val)]
            params['data'][base:] = values[int(vals[-1])]

        return Curve(params)

    def mean(self):
        """
        Could have all sorts of helpful transforms etc.
        """
        try:
            return np.mean(self.data)
        except:
            raise CurveError("You can't do that.")

    def resample(self):
        """
        Resamples a curve to a new basis.
        """
        pass
