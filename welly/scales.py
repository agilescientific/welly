#!/usr/bin/env python
# -*- coding: utf 8 -*-
"""
Custom scales for matplotlib.

:copyright: 2016 Joe Kington

Note: For the two scales, I've set the bounds such that you can never go
beyond a set range.  This gives "stretchy" panning when you reach the ends
of a well.  Sometimes you'll want it, sometimes you won't. In a lot of cases
(e.g. multiple wells or flattening on a marker, etc) you'll want to be able
to go beyond the limits of the well.  In that case, remove the
"limit_range_for_scale" methods below (and BoundedScale entirely) and
use an interpolation function that allows extrapolation beyond the limits
of the input data.
"""
import numpy as np
import matplotlib.scale as mscale
import matplotlib.ticker as mticker
from matplotlib.transforms import Transform


class PiecewiseLinearTransform(Transform):
    """
    Transform between two coordinate systems by interpolating between a
    pre-calculated set of points.  For example, transform between time and
    depth using an average velocity curve.
    """
    input_dims = 1
    output_dims = 1
    is_separable = True
    has_inverse = True

    def __init__(self, x_from, y_to):
        self.xpoints = x_from
        self.ypoints = y_to
        Transform.__init__(self)

    def transform_non_affine(self, x):
        return np.interp(x, self.xpoints, self.ypoints)

    def inverted(self):
        return type(self)(self.ypoints, self.xpoints)


class PiecewiseLinearScale(mscale.ScaleBase):
    """
    Scale based on a piecewise-linear transformation.  For example, this might
    be used to show ticks in two-way time alongside a well log plotted in
    measured depth using a time-depth curve.
    """
    name = 'piecewise'

    def __init__(self, axis, x=None, y=None):
        if x is None or y is None:
            raise ValueError('x and y must be specified for a piecewise scale')
        self.xpoints = x
        self.ypoints = y
        mscale.ScaleBase.__init__(self)

    def get_transform(self):
        return PiecewiseLinearTransform(self.xpoints, self.ypoints)

    def set_default_locators_and_formatters(self, axis):
        axis.set(major_formatter=mticker.ScalarFormatter(),
                 major_locator=mticker.AutoLocator(),
                 minor_locator=mticker.AutoMinorLocator(),
                 minor_formatter=mticker.NullFormatter())

    def limit_range_for_scale(self, vmin, vmax, minpos):
        inverted = vmin > vmax
        if inverted:
            vmax, vmin = vmin, vmax
        vmin = max(vmin, self.xpoints.min())
        vmax = min(vmax, self.xpoints.max())
        if inverted:
            return vmax, vmin
        else:
            return vmin, vmax


class BoundedScale(mscale.LinearScale):
    """
    Linear scale with set bounds that can't be exceeded. Gives a "stretchy"
    panning effect.
    """
    name = 'bounded'

    def __init__(self, axis, vmin=None, vmax=None):
        self.vmin = vmin
        self.vmax = vmax
        mscale.LinearScale.__init__(self, axis)

    def limit_range_for_scale(self, vmin, vmax, minpos):
        inverted = vmin > vmax
        if inverted:
            vmax, vmin = vmin, vmax
        vmin = max(vmin, self.vmin)
        vmax = min(vmax, self.vmax)
        if inverted:
            return vmax, vmin
        else:
            return vmin, vmax

mscale.register_scale(PiecewiseLinearScale)
mscale.register_scale(BoundedScale)
