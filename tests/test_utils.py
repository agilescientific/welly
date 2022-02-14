# -*- coding: utf 8 -*-
"""
Define a suite a tests for the utils.
"""
import numpy as np

from welly.utils import dd2dms, find_nearest, list_and_add, moving_average, moving_avg_conv, normalize, \
    text_colour_for_hex, top_and_tail, extrapolate, get_number_of_decimal_points, get_columns_decimal_formatter


def test_moving_avg():
    """
    Test basic stuff.
    """
    a = np.array([1, 9, 9, 9, 9, 9, 9, 2, 3, 9, 2, 2, 3, 1, 1, 1, 1, 3, 4, 9, 9, 9, 8, 3])
    m = moving_average(a, 5, mode='same')
    t = [4.2, 5.8, 7.4, 9.0, 9.0, 7.6, 6.4, 6.4, 5.0, 3.6, 3.8,
         3.4, 1.8, 1.6, 1.4, 1.4, 2.0, 3.6, 5.2, 6.8, 7.8, 7.6,
         6.4, 5.2]
    assert len(m) == len(a)
    assert np.allclose(m, t)

    # Heads up, these should not be different.
    t = [3.8, 5.6, 7.4, 9.0, 9.0, 7.6, 6.4, 6.4, 5.0, 3.6, 3.8,
         3.4, 1.8, 1.6, 1.4, 1.4, 2.0, 3.6, 5.2, 6.8, 7.8, 7.6,
         5.8, 4.0]
    c = moving_avg_conv(a, 5)
    assert np.allclose(c, t)


def test_top_and_tail():
    """
    Test basic stuff.
    """
    a = np.array([np.nan, np.nan, 9, 9, 9, 9, 9, 2, 3, 9, 2, 1, 1, 3, 4, 9, 9, 9, np.nan, np.nan])
    m = top_and_tail(a)
    t = np.array([9, 9, 9, 9, 9, 2, 3, 9, 2, 1, 1, 3, 4, 9, 9, 9])
    assert len(a) - 4 == len(m)
    assert np.allclose(m, t)


def test_extraplate():
    """
    Test basic stuff.
    """
    a = np.array([np.nan, np.nan, 9, 9, 9, 9, 9, 2, 3, 9, 2, 1, 1, 3, 4, 9, 9, 9, np.nan, np.nan])
    m = extrapolate(a)
    t = np.array([9, 9, 9, 9, 9, 9, 9, 2, 3, 9, 2, 1, 1, 3, 4, 9, 9, 9, 9, 9])
    assert len(a) == len(m)
    assert np.allclose(m, t)


def test_other():
    a = np.array([1, 9, 9, 9, 9, 9, 9, 2, 3, 9, 2, 2, 3, 1, 1, 1, 1, 3, 4, 9, 9, 9, 8, 3])
    t = [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.125, 0.25, 1.0, 0.125, 0.125,
         0.25, 0.0, 0.0, 0.0, 0.0, 0.25, 0.375, 1.0, 1.0, 1.0, 0.875, 0.25]
    assert np.allclose(normalize(a), t)
    assert find_nearest(a, 10) == 9
    assert find_nearest(a, 10, index=True) == 1


def test_list_and_add():
    a = ['this', 'that', 'other']
    b = 'those'
    assert len(list_and_add(b, b)) == 2
    assert len(list_and_add(a, b)) == 4
    assert len(list_and_add(b, a)) == 4


def test_dd2dms():
    dms = dd2dms(123.123)
    assert np.allclose(dms, (123, 7, 22.8))


def test_colour():
    assert text_colour_for_hex('#101010') == '#ffffff'


def test_get_columns_decimal_formatter():
    """
    Test if the columns decimal formatter getter is returning the correct dictionary.
    It should take the highest number of decimal points from every column
    """
    numeric_twodim_arr = np.array([[1.122, 1.1], [1.1, 1.12], [1.11, 1.12]])
    assert get_columns_decimal_formatter(numeric_twodim_arr) == {0: '%.3f', 1: '%.2f'}
    mixed_twodim_arr = np.array([['str'], [np.nan], [1.001]], dtype='object')
    assert get_columns_decimal_formatter(mixed_twodim_arr) == {0: '%.3f'}


def test_get_number_of_decimal_points():
    """
    Test if the number of decimal points for various num/str/nan inputs
    """
    assert get_number_of_decimal_points('string') is None
    assert get_number_of_decimal_points([1.12]) is None
    assert get_number_of_decimal_points(np.nan) is None
    assert get_number_of_decimal_points(1.12) == 2
    assert get_number_of_decimal_points(1) == 0
