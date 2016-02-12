#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines log curves.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np
import matplotlib.pyplot as plt


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

        try:  # treating as a lasio CurveItem object
            self.mnemonic = params.mnemonic
            self.description = params.descr
            self.units = params.unit
            self.data = params.data
            self.basis = basis
        except:
            for k, v in params.items():
                if k and v:
                    setattr(self, k, v)

        self.start, self.stop = self.basis[0], self.basis[-1]
        self.step = self.basis[1] - self.basis[0]

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

    def mean(self):
        """
        Could have all sorts of helpful transforms etc.
        """
        try:
            return np.mean(self.data)
        except:
            raise CurveError("You can't do that.")
