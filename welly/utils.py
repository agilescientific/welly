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
            If ``return_distance==True`` then a tuple is returned, where the
            second value is the distance.
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


def rms(a):
    """
    From ``bruges``

    Calculates the RMS of an array.

    :param a: An array.

    :returns: The RMS of the array.
    """

    return np.sqrt(np.sum(a**2.0)/a.size)


def moving_average(a, length, mode='valid'):
    """
    From ``bruges``

    Computes the mean in a moving window. Naive implementation.

    Example:
        >>> test = np.array([1,9,9,9,9,9,9,2,3,9,2,2,3,1,1,1,1,3,4,9,9,9,8,3])
        >>> moving_average(test, 7, mode='same')
        [ 4.4285714  5.571428  6.7142857  7.8571428  8.          7.1428571
          7.1428571  6.142857  5.1428571  4.2857142  3.1428571  3.
          2.7142857  1.571428  1.7142857  2.          2.857142  4.
          5.1428571  6.142857  6.4285714  6.1428571  5.7142857  4.5714285 ]

    TODO:
        Other types of average.
    """
    pad = np.floor(length/2)

    if mode == 'full':
        pad *= 2

    # Make a padded version, paddding with first and last values
    r = np.empty(a.shape[0] + 2*pad)
    r[:pad] = a[0]
    r[pad:-pad] = a
    r[-pad:] = a[-1]

    # Cumsum with shifting trick
    s = np.cumsum(r, dtype=float)
    s[length:] = s[length:] - s[:-length]
    out = s[length-1:]/length

    # Decide what to return
    if mode == 'same':
        if out.shape[0] != a.shape[0]:
            # If size doesn't match, then interpolate.
            out = (out[:-1, ...] + out[1:, ...]) / 2
        return out
    elif mode == 'valid':
        return out[pad:-pad]
    else:  # mode=='full' and we used a double pad
        return out


def moving_avg_conv(a, length):
    """
    From ``bruges``

    Moving average via convolution. Seems slower than naive.
    """
    boxcar = np.ones(length)/length
    return np.convolve(a, boxcar, mode="same")


def normalize(a, new_min=0.0, new_max=1.0):
    """
    From ``bruges``

    Normalize an array to [0,1] or to
    arbitrary new min and max.

    :param a: An array.
    :param new_min: A float to be the new min, default 0.
    :param new_max: A float to be the new max, default 1.

    :returns: The normalized array.
    """
    n = (a - np.amin(a)) / np.amax(a - np.amin(a))
    return n * (new_max - new_min) + new_min


def top_and_tail(*arrays):
    """
    From ``bruges``

    Top and tail all arrays to the non-NaN extent of the first array.

    E.g. crop the NaNs from the top and tail of a well log.
    """
    if len(arrays) > 1:
        for arr in arrays[1:]:
            assert len(arr) == len(arrays[0])
    nans = np.where(~np.isnan(arrays[0]))[0]
    first, last = nans[0], nans[-1]
    ret_arrays = []
    for array in arrays:
        ret_arrays.append(array[first:last+1])
    return ret_arrays


def extrapolate(a):
    """
    From ``bruges``

    Extrapolate up and down an array from the first and last non-NaN samples.

    E.g. Continue the first and last non-NaN values of a log up and down.
    """
    nans = np.where(~np.isnan(a))[0]
    first, last = nans[0], nans[-1]
    a[:first] = a[first]
    a[last + 1:] = a[last]
    return a
