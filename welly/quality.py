"""
Quality functions for welly.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import copy

import numpy as np
from scipy.spatial.distance import pdist, squareform

from . import utils


def qc_curve_group_well(well, tests, keys=None, alias=None):
    """
    Run tests on a cohort of curves.

    Args:
        well (welly.well.Well): Well object.
        tests (dict): a dictionary of tests, mapping mnemonics to lists of
            tests. Two special keys, `all` and `each` map tests to the set
            of all curves, and to each curve in the well, respectively.
            You only need `all` if the test involves multiple inputs, e.g.
            comparing one curve to another. See example in tests/test_quality.py
        keys (list): a list of the mnemonics to run the tests against.
        alias (dict): an alias dictionary, mapping mnemonics to lists of
            mnemonics. e.g. {'density': ['DEN', 'DENS']}

    Returns:
        dict. Test results for all the curves.
            {curve_name0: {test0: test_result0, ...}, ...}
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
            comparing one curve to another. See example in tests/test_quality.py
        keys (list): a list of the mnemonics to run the tests against.
        alias (dict): an alias dictionary, mapping mnemonics to lists of
            mnemonics. e.g. {'density': ['DEN', 'DENS']}

    Returns:
        dict. The results. Stick to booleans (True = pass) or ints.
            ({curve_name: {test_name: test_result}}

    """
    keys = well._get_curve_mnemonics(keys, alias=alias, curves_only=True)

    r = {k: well.data.get(k).quality(tests, alias) for k in keys}
    s = qc_curve_group_well(well=well, tests=tests, keys=keys, alias=alias)
    for m, results in r.items():
        if m in s:
            results.update(s[m])
    return r


def qc_table_html_well(well, tests, keys=None, alias=None):
    """
    Makes a nice table out of ``qc_data()``.

    Args:
        well (welly.well.Well): Well object.
        tests (dict): a dictionary of tests, mapping mnemonics to lists of
            tests. Two special keys, `all` and `each` map tests to the set
            of all curves, and to each curve in the well, respectively.
            You only need `all` if the test involves multiple inputs, e.g.
            comparing one curve to another. See example in tests/test_quality.py
        keys (list): a list of the mnemonics to run the tests against.
        alias (dict): an alias dictionary, mapping mnemonics to lists of
            mnemonics. e.g. {'density': ['DEN', 'DENS']}

    Returns:
        str. An HTML string for visualization in Jupyter notebook.
            Visualize through IPython.display.HTML(str)
    """
    data = qc_data_well(well=well, tests=tests, keys=keys, alias=alias)
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


def quality_curve(curve, tests, alias=None):
    """
    Run a series of tests and return the corresponding results.

    Args:
        curve (welly.curve.Curve): Curve object.
        tests (list): a list of functions.
        alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
            e.g. {'density': ['DEN', 'DENS']}

    Returns:
        dict. The results. Stick to booleans (True = pass) or ints.
            {test_name: test_result}
    """
    # Gather the test s.
    # First, anything called 'all', 'All', or 'ALL'.
    # Second, anything with the name of the curve we're in now.
    # Third, anything that the alias list has for this curve.
    # (This requires a reverse look-up so it's a bit messy.)

    this_tests = \
        tests.get('each', []) + tests.get('Each', []) + tests.get('EACH', []) \
        + tests.get(curve.mnemonic, []) \
        + utils.flatten_list([tests.get(a) for a in curve.get_alias(alias=alias)])
    this_tests = filter(None, this_tests)

    # If we explicitly set zero tests for a particular key, then this
    # overrides the 'all' and 'alias' tests.
    if not tests.get(curve.mnemonic, 1):
        this_tests = []

    return {test.__name__: test(curve) for test in this_tests}


def quality_score_curve(curve, tests, alias=None):
    """
    Run a series of tests and return the normalized score.

        - 1.0:   Passed all tests.
        - (0-1): Passed a fraction of tests.
        - 0.0:   Passed no tests.
        - -1.0:  Took no tests.

    Args:
        curve (welly.curve.Curve): Curve object.
        tests (list): a list of functions.
        alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
            e.g. {'density': ['DEN', 'DENS']}

    Returns:
        float. The fraction of tests passed, or -1 for 'took no tests'.
    """
    results = quality_curve(curve=curve, tests=tests, alias=alias).values()
    if results:
        return sum(results) / len(results)
    return -1


def qflag_curve(curve, tests, alias=None):
    """
    Run a test and return the corresponding results on a sample-by-sample
    basis.

    Args:
        curve (welly.curve.Curve): Curve object.
        tests (list): a list of functions.
        alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
            e.g. {'density': ['DEN', 'DENS']}

    Returns:
        dict. The results. Stick to booleans (True = pass) or ints.
            {test_name: test_result}
    """
    # Gather the tests.
    # First, anything called 'all', 'All', or 'ALL'.
    # Second, anything with the name of the curve we're in now.
    # Third, anything that the alias list has for this curve.
    # (This requires a reverse look-up so it's a bit messy.)
    this_tests = \
        tests.get('each', []) + tests.get('Each', []) + tests.get('EACH', []) \
        + tests.get(curve.mnemonic, []) \
        + utils.flatten_list([tests.get(a) for a in curve.get_alias(alias=alias)])
    this_tests = filter(None, this_tests)

    return {test.__name__: test(curve) for test in this_tests}


def qflags_curve(curve, tests, alias=None):
    """
    Run a series of tests and return the corresponding results.

    Args:
        curve (welly.curve.Curve): Curve object.
        tests (list): a list of functions.
        alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
            e.g. {'density': ['DEN', 'DENS']}

    Returns:
        dict. The results. Stick to booleans (True = pass) or ints.
            {test_name: test_result}
    """
    # Gather the tests.
    # First, anything called 'all', 'All', or 'ALL'.
    # Second, anything with the name of the curve we're in now.
    # Third, anything that the alias list has for this curve.
    # (This requires a reverse look-up so it's a bit messy.)
    this_tests = \
        tests.get('each', []) + tests.get('Each', []) + tests.get('EACH', []) \
        + tests.get(curve.mnemonic, []) \
        + utils.flatten_list([tests.get(a) for a in curve.get_alias(alias=alias)])
    this_tests = filter(None, this_tests)

    return {test.__name__: test(curve) for test in this_tests}


# All
# Runs on multiple curves
def no_similarities(well, keys, alias):
    X = well.data_as_matrix(keys=keys, alias=alias)
    d = squareform(pdist(X.T, 'hamming'))
    return list(np.sum(d, axis=1) > (len(keys) - 1.5))


# Each
# Single curve
def not_empty(curve):
    """
    If curve.df is not empty, return True.
    """
    return not curve.df.empty


def all_positive(curve):
    """
    Define it this way to avoid NaN problem.
    """
    result = np.nanmin(curve.df.values) >= 0
    return bool(result)


def no_nans(curve):
    """
    Check for NaNs anywhere at all in the curve, even the top or bottom.
    """
    number_of_nan = curve.df.isnull().sum().sum()
    return not bool(number_of_nan)


def no_gaps(curve):
    """
    Check for gaps, after ignoring any NaNs at the top and bottom.
    """
    tnt = utils.top_and_tail(curve.as_numpy())
    return not any(np.isnan(tnt))


def no_flat(curve):

    def consecutive(data, stepsize=1):
        return np.split(data, np.where(np.diff(data) != stepsize)[0] + 1)

    curve_value = curve.as_numpy()
    tolerance = max(3, curve_value.size // 100)
    zeros = np.where(np.diff(curve_value) == 0)[0]
    tolerated = [a.size < tolerance for a in consecutive(zeros)]
    return np.all(tolerated)


def no_monotonic(curve):
    """no_flat on the differences of the curve"""
    curve_diff = copy.deepcopy(curve)
    curve_diff.df = curve.df.diff().iloc[1:]

    return no_flat(curve_diff)


def all_above(value):
    def all_above(curve):
        curve_data = curve.as_numpy()
        return all(curve_data[~np.isnan(curve_data)] > value)

    return all_above


def all_below(value):
    def all_below(curve):
        curve_data = curve.as_numpy()
        return all(curve_data[~np.isnan(curve_data)] < value)

    return all_below


def all_between(lower, upper):
    def all_between(curve):
        curve_data = curve.as_numpy()
        l = all(lower < curve_data[~np.isnan(curve_data)])
        u = all(upper > curve_data[~np.isnan(curve_data)])
        return l and u

    return all_between


def mean_above(value):
    def mean_above(curve):
        curve_data = curve.as_numpy()
        return bool(np.nanmean(curve_data) > value)

    return mean_above


def mean_below(value):
    def mean_below(curve):
        curve_data = curve.as_numpy()
        return bool(np.nanmean(curve_data) < value)

    return mean_below


def mean_between(lower, upper):
    def mean_between(curve):
        curve_data = curve.as_numpy()
        l = lower < np.nanmean(curve_data)
        u = upper > np.nanmean(curve_data)
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
        diff = np.abs(curve.as_numpy() - curve.despike().as_numpy())
        return np.count_nonzero(diff) < tolerance

    return no_spikes


def fraction_not_nans(curve):
    """
    Returns the fraction of the curve extents that are good (non-nan data).
    """
    return 1 - curve.df.isna().sum().sum() / curve.df.__len__() * curve.df.columns.__len__()


def fraction_not_zeros(curve):
    """
    Returns the fraction of the curve extents that are not zeros.
    """
    return np.count_nonzero(curve.df.values) / curve.df.__len__() * curve.df.columns.__len__()


def fraction_within_range(xmin, xmax):
    def fraction_within_range(curve):
        curve_data = curve.as_numpy()
        nsamps = len(curve_data)
        finite = np.nan_to_num(curve_data)
        greaterthan_max = len(np.extract(finite > xmax, finite))
        lessthan_min = len(np.extract(finite < xmin, finite))
        return 1 - ((greaterthan_max + lessthan_min) / nsamps)

    return fraction_within_range


def count_spikes(curve):
    diff = np.abs(curve.as_numpy() - curve.despike().as_numpy())
    return np.count_nonzero(diff)


def spike_locations(curve):
    """
    Return the indicies of the spikes.
    """
    return
