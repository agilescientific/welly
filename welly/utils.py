#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions for welly.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np


def null(x):
    """
    Null function. Used for default in functions that can apply a user-
    supplied function to data before returning.
    """
    return x


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
    given value. Optionally also return the fractional distance of the given
    value from that previous value.

    Args:
        a (ndarray)
        value (float)
        index (bool): whether to return the index instead of the array value.
            Default: False.
        return_distance(bool): whether to return the fractional distance from
            the nearest value to the specified value. Default: False.

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


def find_edges(a):
    """
    Return two arrays: one of the changes, and one of the values.

    Returns:
        tuple: Two ndarrays, tops and values.
    """
    edges = a[1:] == a[:-1]
    tops = np.where(~edges)[0] + 1
    tops = np.append(0, tops)
    values = a[tops]

    return tops, values


def lasio_get(l, section, item=None, attrib=None, default=None):
    """
    Gets attributes not found by lasio
    """

    try:
        if item is None:
            return getattr(l, section)
        elif attrib is None:
            return getattr(l, section)[item]
        return getattr(l, section)[item][attrib]
    except KeyError:
        return default
