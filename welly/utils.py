#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions for welly.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np


def parabolic(f, x):
    """
    Interpolation. From ageobot, from somewhere else.
    """
    xv = 1/2. * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 1/4. * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)


def linear(u, v, d):
    """
    Linear interpolation.
    Args:
        u (float)
        v (float)
        d (float): the relative distance between the two to return.

    Returns:
        float. The interpolated value.
    """
    return u + d*(v-u)


def find_nearest(a, value, index=False):
    """
    Find the array value, or index of the array value, closest to some given
    value.

    Args:
        a (ndarray)
        value (float)
        index (bool): whether to return the index instead of the array value.

    Returns:
        float. The array value (or index, as int) nearest the specified value.
    """
    i = np.abs(a - value).argmin()
    if index:
        return i
    else:
        return a[i]


def find_previous(a, value, index=False, return_distance=False):
    """
    Find the nearest array value, or index of the array value, before some
    given value.

    Args:
        a (ndarray)
        value (float)
        index (bool): whether to return the index instead of the array value.

    Returns:
        float. The array value (or index, as int) before the specified value.
    """
    b = a - value
    i = np.where(b > 0)[0][0]
    d = (value - a[i-1]) / (a[i] - a[i-1])
    if index:
        if return_distance:
            return i - 1, d
        else:
            return i - 1
    else:
        if return_distance:
            return a[i - 1], d
        else:
            return a[i - 1]
