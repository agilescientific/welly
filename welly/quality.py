#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quality functions for welly.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np

from . import utils


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
    tnt = utils.top_and_tail(curve)[0]  # top_and_tail returns a list
    return not any(np.isnan(tnt))


def no_flat(curve):
    tolerance = max(3, curve.size//100)
    zeros = np.where(np.diff(curve) == 0)[0]
    return zeros.size < tolerance


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


def check_units(list_of_units):
    def check_units(curve):
        return curve.units in list_of_units
    return check_units


def no_spikes(tolerance):  # tolerance is 'number of spiky samples allowed'
    def no_spikes(curve):
        diff = np.abs(curve - curve.despike())
        return np.count_nonzero(diff) < tolerance
    return no_spikes
