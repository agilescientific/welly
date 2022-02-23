"""
Utility functions for welly.

Copyright: 2021 Agile Scientific
Licence: Apache 2.0
"""
import decimal
import functools
import glob
import inspect
import re
import warnings

import matplotlib.cbook as cbook
import matplotlib.pyplot as plt
import numpy as np

from welly.fields import las_objects

# Most common numeric null values representation in LAS files.
NULL_VALUES = [9999.25, -9999.25, -9999, 9999, 999.25, -999.25]


def alias_map(alias):
    """
    Reverse an alias dictionary, returning a new dict mapping mnemonics
    to alias names.

    Args:
        alias (dict): An alias dictionary.
    
    Returns:
        dict: A new dictionary mapping mnemonics to alias names.

    Example:
        >>> alias = {'Sonic': ['DT', 'DT4P'], 'Caliper': ['HCAL', 'CALI']}
        >>> alias_map(alias)
        {'DT': 'Sonic', 'DT4P': 'Sonic', 'HCAL': 'Caliper', 'CALI': 'Caliper'}
    """
    if alias is None:
        return {}
    return {v: k for k, vs in alias.items() for v in vs}


def deprecated(instructions):
    """
    Flags a method as deprecated. This decorator can be used to mark functions
    as deprecated. It will result in a warning being emitted when the function
    is used.

    Args:
        instructions (str): A human-friendly string of instructions, such
            as: 'Please migrate to add_proxy() ASAP.'

    Returns:
        The decorated function.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = 'Call to deprecated function {}. {}'.format(
                func.__name__,
                instructions)

            frame = inspect.currentframe().f_back

            warnings.warn_explicit(message,
                                   category=DeprecationWarning,
                                   filename=inspect.getfile(frame.f_code),
                                   lineno=frame.f_lineno)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def bbox(points):
    x, y = zip(*points)
    return [(min(x), min(y)), (max(x), max(y))]


def aspect(points):
    """
    Aspect like 2:1 is twice as wide as high.

    This function returns the WIDTH per unit height.
    """
    (minx, miny), (maxx, maxy) = bbox(points)
    return (maxx - minx) / (maxy - miny)


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


def flatten_list(L):
    """
    Flattens a list. For example:

        >> flatten_list([1, 2, [3, 4], [5, [6, 7]]])
        [1, 2, 3, 4, 5, 6, 7]
    """
    return list(cbook.flatten(L)) if L else L


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


def get_header_item(header,
                    section,
                    item,
                    attrib='value',
                    default=None,
                    remap=None,
                    funcs=None):
    """
    Grabs a header item from a header pd.DataFrame and optionally renames and
    transforms it.

    Args:
        header (pd.DataFrame): Header from LAS file parsed to tabular form.
            See `las.from_las()` for more information.
        section (str): The LAS section to grab from, eg ``well``
        item (str): The item in the LAS section to grab from, eg ``name``
        attrib (str): The attribute of the item to grab, eg ``value``
        default (str): What to return instead.
        remap (dict): Optional. A dict of 'old': 'new' LAS field names.
        funcs (dict): Optional. A dict of 'las field': function() for
            implementing a transform before loading. Can be a lambda.

    Returns:
        The requested, optionally transformed, item.
    """
    remap = remap or {}
    item_to_fetch = remap.get(item, item)

    if item_to_fetch is None:
        return None

    try:
        result = header[(header.mnemonic == item_to_fetch) &
                        (header.section == las_objects[section])][attrib].values[0]
    except Exception:
        return default

    # apply input function on item
    if funcs is not None:
        f = funcs.get(item, null)
        result = f(result)

    return result


def parabolic(f, x):
    """
    Interpolation. From ageobot, from somewhere else.
    """
    xv = 1 / 2. * (f[x - 1] - f[x + 1]) / (f[x - 1] - 2 * f[x] + f[x + 1]) + x
    yv = f[x] - 1 / 4. * (f[x - 1] - f[x + 1]) * (xv - x)
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
    return u + d * (v - u)


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
    d = (value - a[i - 1]) / (a[i] - a[i - 1])
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

    return np.sqrt(np.sum(a ** 2.0) / a.size)


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
    pad = np.floor(length / 2)

    if mode == 'full':
        pad *= 2
    pad = int(pad)

    # Make a padded version, paddding with first and last values
    r = np.zeros(a.shape[0] + 2 * pad)
    r[:pad] = a[0]
    r[pad:-pad] = a
    r[-pad:] = a[-1]

    # Cumsum with shifting trick
    s = np.cumsum(r, dtype=float)
    s[length:] = s[length:] - s[:-length]
    out = s[length - 1:] / length

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
    boxcar = np.ones(length) / length
    return np.convolve(a, boxcar, mode="same")


def nan_idx(y):
    """
    Helper to handle indices and logical indices of NaNs.

    Args:
        y (ndarray): 1D array with possible NaNs

    Returns:
        nans, logical indices of NaNs
        index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices

    Example:
        >> # linear interpolation of NaNs
        >> nans, x = nan_helper(y)
        >> y[nans] = np.interp(x(nans), x(~nans), y[~nans])
    """
    return np.isnan(y), lambda z: z.nonzero()[0]


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


def top_and_tail(a):
    """
    Remove the NaNs from the top and tail (only) of a well log.

    Args:
        a (ndarray): An array.

    Returns:
        ndarray: The top and tailed array.
    """
    if np.all(np.isnan(a)):
        return np.array([])
    nans = np.where(~np.isnan(a))[0]
    last = None if nans[-1] + 1 == a.size else nans[-1] + 1
    return a[nans[0]:last]


def dms2dd(dms):
    """
    DMS to decimal degrees.

    Args:
        dms (list). d must be negative for S and W.

    Returns:
        float.
    """
    d, m, s = dms
    return d + m / 60. + s / 3600.


def dd2dms(dd):
    """
    Decimal degrees to DMS.

    Args:
        dd (float). Decimal degrees.

    Returns:
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
    t = np.linspace(-int(length / 2), int((length - dt) / 2), int(length / dt))
    y = (1. - 2. * (np.pi ** 2) * (f ** 2) * (t ** 2)) * np.exp(-(np.pi ** 2) * (f ** 2) * (t ** 2))
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

    return tuple(int(h[i:i + l // 3], 16) for i in range(0, l, l // 3))


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


def to_filename(path):
    """
    Convert string/pathlib.Path to string.

    Args:
        path (str/pathlib.Path): filename

    Returns:
        str: filename
    """
    try:
        from pathlib import Path
    except ImportError:
        return path

    if isinstance(path, Path):
        return path.absolute().__str__()
    else:
        return path


def get_columns_decimal_formatter(data, null_value=None):
    """
    Get the column decimal point formatter from the two-dimensional numpy.ndarray.
    Get the number of decimal points from columns with numerical values (float or int).
    Take the highest number of decimal points of the column values.
    The dictionary maps the column order of occurrence to the numerical formatter function.
    If a column has no numerical values, don't create a mapping for that column in the dictionary.

    For example, an input np.ndarray might look like this.

        - 1st column values: most occurring 2 decimal points
        - 2nd column values: most occurring 5 decimal points
        - 3rd column values: most occurring 10 decimal points

    This will return the following.
    
        column_fmt = {0: '%.2f', 1: '%.5f', 2: '%.10f'}

    Args:
        data (numpy.ndarray): two-dimensional array with floats and/or ints (columns and rows).
        null_value (float): Optional. A float that represents null/NaN in the column values from which we do not take
                            the number of decimals.

    Returns:
        column_fmt (dict): Mapping of order of column occurrence to most occurring decimal point formatting function
    """
    if null_value:
        NULL_VALUES.append(null_value)

    column_fmt = {}

    # iterate over the transpose to iterate over columns
    for i, arr in enumerate(data.T):

        # get most occurring decimal points for the values in the column, excluding null representation
        column_values_n_decimal_points = [get_number_of_decimal_points(x) for x in arr if isinstance(x, (int, float))
                                          and x not in NULL_VALUES]

        # remove None values from list in place
        column_values_n_decimal_points = [x for x in column_values_n_decimal_points if x is not None]

        if len(column_values_n_decimal_points) > 0:
            # get the highest number of decimal points that were found in column
            mode = max(column_values_n_decimal_points)

            if mode:
                # create string formatter and map in dictionary to curve number of occurrence
                column_fmt[i] = '%.{}f'.format(mode)

    return column_fmt


def get_number_of_decimal_points(value):
    """
    Get the number of decimal points from a numeric value (float or int).

    Args:
        value (float or int): Numeric value
    Returns:
        n_decimals (int): Number of decimal points if value is of type float or int, otherwise return None.
    """
    if isinstance(value, (int, float)) and not np.isnan(value):
        # get and return the number of decimal points from the value
        return -decimal.Decimal(str(value)).as_tuple().exponent
    else:
        return None


def get_step_from_array(arr):
    """
    Gets the 'step' or increment of the array. Requires numeric values in array

    Args:
        arr (np.array): The array

    Returns:
        Float. If the index is numeric and equally sampled
        0. If the index is numeric and not equally sampled
        None. If the index is not numeric
    """
    # compute differences between subsequent elements in index array
    dif = np.diff(arr)
    if np.allclose(dif - np.mean(dif), np.zeros_like(dif)):
        # index evenly sampled
        return np.nanmedian(dif)
    else:
        # index unevenly sampled so cannot derive `step`
        return 0
