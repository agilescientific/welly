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

        # Set a couple more.
        self.start, self.stop = self.basis[0], self.basis[-1]
        self.step = self.basis[1] - self.basis[0]

    @classmethod
    def from_lasio_curve(cls, curve, basis=None, run=-1):
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

        return cls(params)

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

    def plot(self):
        """
        Plot a curve.
        """
        fig = plt.figure(figsize=(2, 10))
        ax = fig.add_subplot(111)
        ax.plot(self.data, self.basis)
        plt.title(self.mnemonic)
        ax.set_ylim([self.stop, self.start])
        return

    def segment(self, depths, return_basis=False):
        """
        Returns a 'segment' (chunk or slice) of a curve.
        """
        raise NotImplementedError("We haven't written this function yet!")

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

    def block(self, bins=None, n_bins=0, right=False, function=None):
        """
        Block a log based on number of bins, or on cutoffs.

        Wraps ``numpy.digitize()``
        """
        if bins is None and n_bins == 0:
            bins = np.mean(self.data)

        # We'll return a copy.
        params = self.__dict__.copy()

        if n_bins != 0:
            bins = np.linspace(np.amin(self.data), np.amax(self.data), 4+1)
            bins = bins[:-1]

        try:  # To use cutoff as a list.
            params['data'] = np.digitize(self.data, bins, right)
        except ValueError:  # It's just a number.
            params['data'] = np.digitize(self.data, [bins], right)

        if function is None:
            # Then we're done already.
            print('no reduce')
            return Curve(params)

        # Else carry on... Set the function for reducing.
        f = function or utils.null
        print(f.__name__)

        # Find the tops of the 'zones'.
        tops, _ = utils.find_edges(params['data'])

        # Transform each segment in turn, then deal with the last segment.
        for top, base in zip(tops[:-1], tops[1:]):
            params['data'][top:base] = f(self.data[top:base])
        params['data'][base:] = f(self.data[base:])

        return Curve(params)

    def mean(self):
        """
        Could have all sorts of helpful transforms etc.
        """
        try:
            return np.mean(self.data)
        except:
            raise CurveError("You can't do that.")
