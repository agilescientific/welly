# -*- coding: utf-8 -*-
"""
Utility functions for welly.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import re
import glob

import numpy as np
import matplotlib.pyplot as plt


def round_to_n(x, n):
    """
    Round to sig figs
    """
    return round(x, -int(np.floor(np.log10(x))) + (n - 1))


def null(x):
    """
    Null function. Used for default in functions that can apply a user-
    supplied function to data before returning.
    """
    return x


def null_default(x):
    """
    Null function. Used for default in functions that can apply a user-
    supplied function to data before returning.
    """
    def null(y):
        return x

    return null


def skip(x):
    """
    Always returns None.
    """
    return


def are_close(x, y):
    return abs(x - y) < 0.00001


def sharey(axes):
    """
    Shared axes limits without shared locators, ticks, etc.

    By Joe Kington
    """
    linker = Linker(axes)
    for ax in axes:
        ax._linker = linker


def unsharey(ax):
    """
    Remove sharing from an axes.

    By Joe Kington
    """

    ax._linker.unlink(ax)
    ax._linker = None


class Linker(object):
    """
    Keeps y-limits of a sequence of axes in sync when panning/zooming.

    By Joe Kington
    """
    def __init__(self, axes):
        self.axes = axes
        self._cids = {}
        for ax in self.axes:
            self.link(ax)

    def unlink(self, ax):
        ax.callbacks.disconnect(self._cids.pop(ax))

    def link(self, ax):
        self._cids[ax] = ax.callbacks.connect('ylim_changed', self.rescale)

    def rescale(self, axes):
        limits = axes.yaxis._scale.get_transform().transform(axes.get_ylim())
        for ax in self.axes:
            lim = ax.yaxis._scale.get_transform().inverted().transform(limits)
            ax.set_ylim(lim, emit=False, auto=None)

            # Note - This is specifically for this application!
            fix_ticks(ax)


def fix_ticks(ax):
    """
    Center ticklabels and hide any outside axes limits.

    By Joe Kington
    """
    plt.setp(ax.get_yticklabels(), ha='center', x=0.5,
             transform=ax._yaxis_transform)

    # We'll still wind up with some tick labels beyond axes limits for reasons
    # I don't fully understand...
    limits = ax.get_ylim()
    for label, loc in zip(ax.yaxis.get_ticklabels(), ax.yaxis.get_ticklocs()):
        if loc < min(limits) or loc > max(limits):
            label.set(visible=False)
        else:
            label.set(visible=True)


def flatten_list(l):
    """
    Unpacks lists in a list:

        [1, 2, [3, 4], [5, [6, 7]]]

    becomes

        [1, 2, 3, 4, 5, 6, 7]

    http://stackoverflow.com/a/12472564/3381305
    """
    if (l == []) or (l is None):
        return l
    if isinstance(l[0], list):
        return flatten_list(l[0]) + flatten_list(l[1:])
    return l[:1] + flatten_list(l[1:])


def list_and_add(a, b):
    """
    Concatenate anything into a list.

    Args:
        a: the first thing
        b: the second thing

    Returns:
        list. All the things in a list.
    """
    if not isinstance(b, list):
        b = [b]
    if not isinstance(a, list):
        a = [a]
    return a + b


def lasio_get(l,
              section,
              item,
              attrib='value',
              default=None,
              remap=None,
              funcs=None):
    """
    Grabs, renames and transforms stuff from a lasio object.

    Args:
        l (lasio): a lasio instance.
        section (str): The LAS section to grab from, eg ``well``
        item (str): The item in the LAS section to grab from, eg ``name``
        attrib (str): The attribute of the item to grab, eg ``value``
        default (str): What to return instead.
        remap (dict): Optional. A dict of 'old': 'new' LAS field names.
        funcs (dict): Optional. A dict of 'las field': function() for
            implementing a transform before loading. Can be a lambda.

    Returns:
        The transformed item.
    """
    remap = remap or {}
    item_to_fetch = remap.get(item, item)
    if item_to_fetch is None:
        return None

    try:
        obj = getattr(l, section)
        result = getattr(obj, item_to_fetch)[attrib]
    except:
        return default

    if funcs is not None:
        f = funcs.get(item, null)
        result = f(result)

    return result


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


def normalize(a, new_min=0.0, new_max=1.0):
    """
    From ``bruges``

    Normalize an array to [0,1] or to arbitrary new min and max.

    Args:
        a (ndarray)
        new_min (float): the new min, default 0.
        new_max (float): the new max, default 1.

    Returns:
        ndarray. The normalized array.
    """

    n = (a - np.amin(a)) / np.amax(a - np.amin(a))
    return n * (new_max - new_min) + new_min


def moving_average(a, length, mode='valid'):
    """
    From ``bruges``

    Computes the mean in a moving window. Naive implementation.

    Example:
        >>> test = np.array([1,9,9,9,9,9,9,2,3,9,2,2,3,1,1,1,1,3,4,9,9,9,8,3])
        >>> moving_average(test, 7, mode='same')
        [ 4.42857143,  5.57142857,  6.71428571,  7.85714286,  8.        ,
        7.14285714,  7.14285714,  6.14285714,  5.14285714,  4.28571429,
        3.14285714,  3.        ,  2.71428571,  1.57142857,  1.71428571,
        2.        ,  2.85714286,  4.        ,  5.14285714,  6.14285714,
        6.42857143,  6.42857143,  6.28571429,  5.42857143]

    TODO:
        Other types of average.
    """
    pad = np.floor(length/2)

    if mode == 'full':
        pad *= 2
    pad = int(pad)

    # Make a padded version, paddding with first and last values
    r = np.zeros(a.shape[0] + 2*pad)
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


def dms2dd(dms):
    """
    DMS to decimal degrees.

    Args:
        dms (list). d must be negative for S and W.

    Return:
        float.
    """
    d, m, s = dms
    return d + m/60. + s/3600.


def dd2dms(dd):
    """
    Decimal degrees to DMS.

    Args:
        dd (float). Decimal degrees.

    Return:
        tuple. Degrees, minutes, and seconds.
    """
    m, s = divmod(dd * 3600, 60)
    d, m = divmod(m, 60)
    return int(d), int(m), s


def ricker(f, length, dt):
    """
    A Ricker wavelet.

    Args:
        f (float): frequency in Haz, e.g. 25 Hz.
        length (float): Length in s, e.g. 0.128.
        dt (float): sample interval in s, e.g. 0.001.

    Returns:
        tuple. time basis, amplitude values.
    """
    t = np.linspace(-length/2, (length-dt)/2, length/dt)
    y = (1. - 2.*(np.pi**2)*(f**2)*(t**2))*np.exp(-(np.pi**2)*(f**2)*(t**2))
    return t, y


def hex_to_rgb(hexx):
    """
    Utility function to convert hex to (r,g,b) triples.
    http://ageo.co/1CFxXpO

    Args:
        hexx (str): A hexadecimal colour, starting with '#'.

    Returns:
        tuple: The equivalent RGB triple, in the range 0 to 255.
    """
    h = hexx.strip('#')
    l = len(h)

    return tuple(int(h[i:i+l//3], 16) for i in range(0, l, l//3))


def hex_is_dark(hexx, percent=50):
    """
    Function to decide if a hex colour is dark.

    Args:
        hexx (str): A hexadecimal colour, starting with '#'.

    Returns:
        bool: The colour's brightness is less than the given percent.
    """
    r, g, b = hex_to_rgb(hexx)
    luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 2.55  # per ITU-R BT.709

    return (luma < percent)


def text_colour_for_hex(hexx, percent=50, dark='#000000', light='#ffffff'):
    """
    Function to decide what colour to use for a given hex colour.

    Args:
        hexx (str): A hexadecimal colour, starting with '#'.

    Returns:
        bool: The colour's brightness is less than the given percent.
    """
    return light if hex_is_dark(hexx, percent=percent) else dark


def get_lines(handle, line):
    """
    Get zero-indexed line from an open file-like.
    """
    for i, l in enumerate(handle):
        if i == line:
            return l


def find_file(pattern, path):
    """
    A bit like grep. Finds a pattern, looking in path. Returns the filename.
    """
    for fname in glob.iglob(path):
        with open(fname) as f:
            if re.search(pattern, f.read()):
                return fname
    return
