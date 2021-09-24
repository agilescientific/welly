"""
Quality functions for welly.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import numpy as np
from scipy.spatial.distance import pdist, squareform

from . import utils


# All
# Runs on multiple curves
def no_similarities(well, keys, alias):
    X = well.data_as_matrix(keys=keys, alias=alias)
    d = squareform(pdist(X.T, 'hamming'))
    return list(np.sum(d, axis=1) > (len(keys) - 1.5))


# Each
# Single curve
def not_empty(curve):
    return not bool(np.all(np.isnan(curve)))


def all_positive(curve):
    """
    Define it this way to avoid NaN problem.
    """
    result = np.nanmin(curve) >= 0
    return bool(result)


def no_nans(curve):
    """
    Check for NaNs anywhere at all in the curve, even the top or bottom.
    """
    return not any(np.isnan(curve))


def no_gaps(curve):
    """
    Check for gaps, after ignoring any NaNs at the top and bottom.
    """
    tnt = utils.top_and_tail(curve)
    return not any(np.isnan(tnt))


def no_flat(curve):

    def consecutive(data, stepsize=1):
        return np.split(data, np.where(np.diff(data) != stepsize)[0]+1)

    tolerance = max(3, curve.size//100)
    zeros = np.where(np.diff(curve) == 0)[0]
    tolerated = [a.size < tolerance for a in consecutive(zeros)]
    return np.all(tolerated)


def no_monotonic(curve):
    return no_flat(np.diff(curve))


def all_above(value):
    def all_above(curve):
        return all(curve[~np.isnan(curve)] > value)
    return all_above


def all_below(value):
    def all_below(curve):
        return all(curve[~np.isnan(curve)] < value)
    return all_below


def all_between(lower, upper):
    def all_between(curve):
        l = all(lower < curve[~np.isnan(curve)])
        u = all(upper > curve[~np.isnan(curve)])
        return l and u
    return all_between


def mean_above(value):
    def mean_above(curve):
        return bool(np.nanmean(curve) > value)
    return mean_above


def mean_below(value):
    def mean_below(curve):
        return bool(np.nanmean(curve) < value)
    return mean_below


def mean_between(lower, upper):
    def mean_between(curve):
        l = lower < np.nanmean(curve)
        u = upper > np.nanmean(curve)
        return bool(l and u)
    return mean_between


def check_units(list_of_units):
    def check_units(curve):
        return curve.units in list_of_units
    return check_units


def no_spikes(tolerance):
    """
    Arg ``tolerance`` is the number of spiky samples allowed.
    """
    def no_spikes(curve):
        diff = np.abs(curve - curve.despike())
        return np.count_nonzero(diff) < tolerance
    return no_spikes


def fraction_not_nans(curve):
    """
    Returns the fraction of the curve extents that are good (non-nan data).
    """
    return 1 - (len(np.extract(np.isnan(curve), curve)) / len(curve))


def fraction_not_zeros(curve):
    """
    Returns the fraction of the curve extents that are not zeros.
    """
    return np.count_nonzero(curve) / len(curve)


def fraction_within_range(xmin, xmax):
    def fraction_within_range(curve):
        nsamps = len(curve)
        finite = np.nan_to_num(curve)
        greaterthan_max = len(np.extract(finite > xmax, finite))
        lessthan_min = len(np.extract(finite < xmin, finite))
        return 1 - ((greaterthan_max + lessthan_min) / nsamps)
    return fraction_within_range


def count_spikes(curve):
    diff = np.abs(curve - curve.despike())
    return np.count_nonzero(diff)


def spike_locations(curve):
    """
    Return the indicies of the spikes.
    """
    return


def qc_curve_group_well(well, tests, keys=None, alias=None):
    """
    Run tests on a cohort of curves.

    Args:
        tests (dict): a dictionary of tests, mapping mnemonics to lists of
            tests. Two special keys, `all` and `each` map tests to the set
            of all curves, and to each curve in the well, respectively.
            You only need `all` if the test involves multiple inputs, e.g.
            comparing one curve to another.
        keys (list): a list of the mnemonics to run the tests against.
        alias (dict): an alias dictionary, mapping mnemonics to lists of
            mnemonics.

    Returns:
        dict.
    """
    keys = well._get_curve_mnemonics(keys, alias=alias)

    if not keys:
        return {}

    all_tests = tests.get('all', tests.get('All', tests.get('ALL', [])))
    data = {test.__name__: test(well, keys, alias) for test in all_tests}

    results = {}
    for i, key in enumerate(keys):
        this = {}
        for test, result in data.items():
            this[test] = result[i]
        results[key] = this
    return results


def qc_data_well(well, tests, keys=None, alias=None):
    """
    Run a series of tests against the data and return the corresponding
    results.

    Args:
        tests (dict): a dictionary of tests, mapping mnemonics to lists of
            tests. Two special keys, `all` and `each` map tests to the set
            of all curves, and to each curve in the well, respectively.
            You only need `all` if the test involves multiple inputs, e.g.
            comparing one curve to another.
        keys (list): a list of the mnemonics to run the tests against.
        alias (dict): an alias dictionary, mapping mnemonics to lists of
            mnemonics.

    Returns:
        list. The results. Stick to booleans (True = pass) or ints.
    """
    keys = well._get_curve_mnemonics(keys, alias=alias, curves_only=False)
    r = {k: well.data.get(k).quality(tests, alias) for k in keys}
    s = well.qc_curve_group(tests, keys, alias=alias)
    for m, results in r.items():
        if m in s:
            results.update(s[m])
    return r


def qc_table_html_well(well, tests, keys=None, alias=None):
    """
    Makes a nice table out of ``qc_data()``

    Returns:
        str. An HTML string.
    """
    data = well.qc_data(tests, keys=keys, alias=alias)
    all_tests = [list(d.keys()) for d in data.values()]
    tests = list(set(utils.flatten_list(all_tests)))

    # Header row.
    r = '</th><th>'.join(['Curve', 'Passed', 'Score'] + tests)
    rows = '<tr><th>{}</th></tr>'.format(r)

    styles = {
        True: "#CCEECC",  # Green
        False: "#FFCCCC",  # Red
    }

    # Quality results.
    for curve, results in data.items():

        if results:
            norm_score = sum(results.values()) / len(results)
        else:
            norm_score = -1

        rows += '<tr><th>{}</th>'.format(curve)
        rows += '<td>{} / {}</td>'.format(sum(results.values()), len(results))
        rows += '<td>{:.3f}</td>'.format(norm_score)

        for test in tests:
            result = results.get(test, '')
            style = styles.get(result, "#EEEEEE")
            rows += '<td style="background-color:{};">'.format(style)
            rows += '{}</td>'.format(result)
        rows += '</tr>'

    html = '<table>{}</table>'.format(rows)
    return html
