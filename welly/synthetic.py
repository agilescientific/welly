"""
Defines a synthetic seismogram.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import numpy as np
import matplotlib.pyplot as plt

from .curve import Curve


class Synthetic(np.ndarray):
    """
    Synthetic seismograms.
    """

    def __new__(cls, data, basis=None, params=None):
        obj = np.asarray(data).view(cls).copy()

        params = params or {}

        for k, v in params.items():
            setattr(obj, k, v)

        if basis is not None:
            setattr(obj, 'start', basis[0])
            setattr(obj, 'step', basis[1]-basis[0])

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

        if obj.size == 1:
            return float(obj)

        self.start = getattr(obj, 'start', 0)
        self.dt = getattr(obj, 'dt', 0.001)
        self.name = getattr(obj, 'name', 'Synthetic')

    @property
    def stop(self):
        """
        Compute stop rather than storing it.
        """
        return self.start + self.shape[0] * self.dt

    @property
    def basis(self):
        """
        Compute basis rather than storing it.
        """
        precision_adj = self.dt / 100
        return np.arange(self.start, self.stop - precision_adj, self.dt)

    def as_curve(self, data):
        """
        Get the synthetic as a Curve, in depth. Facilitates plotting along-
        side other curve data.
        """
        params = {'mnemonic': 'SYN'}

        return Curve(data, **params)

    def plot(self, ax=None, **kwargs):
        """
        Plot a synthetic.

        Args:
            ax (ax): A matplotlib axis.
            legend (Legend): For now, only here to match API for other plot
                methods.

        Returns:
            ax. If you passed in an ax, otherwise None.
        """
        if ax is None:
            fig = plt.figure(figsize=(2, 10))
            ax = fig.add_subplot(111)
            return_ax = False
        else:
            return_ax = True

        hypertime = np.linspace(self.start, self.stop, (10 * self.size - 1) + 1)
        hyperamp = np.interp(hypertime, self.basis, self)

        ax.plot(hyperamp, hypertime, 'k', **kwargs)
        ax.fill_betweenx(hypertime, hyperamp, 0, hyperamp > 0.0, facecolor='k', lw=0)
        ax.invert_yaxis()
        ax.set_title(self.name)

        if return_ax:
            return ax

        return fig
