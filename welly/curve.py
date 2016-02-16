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
    def __init__(self, params, basis=None):
        """
        Args:
            params (dict or lasio.Curve)
            basis (array-like): An array representing depth.
        """
        if basis is None:
            raise CurveError('you must provide a depth basis.')

        # Take care of the most important things.
        self.basis = basis
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
        params['mnemonic'] = curve.mnemonic
        params['description'] = curve.descr
        params['units'] = curve.unit
        params['data'] = curve.data
        params['run'] = run

        return cls(params, basis=basis)

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

    def _read_at_index(self, i):
        """
        Private function. Helper function for ``read_at()``.
        """
        pass

    def read_at(self, d, interpolation='linear', index=False, return_basis=False):
        """
        Read the log at a specific depth.

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

        i, d = utils.find_previous(self.basis, d, index=True, return_distance=True)
        value = method[interpolation](self.data[i], self.data[i+1], d)
        return value

    def mean(self):
        """
        Could have all sorts of helpful transforms etc.
        """
        try:
            return np.mean(self.data)
        except:
            raise CurveError("You can't do that.")
