# -*- coding: utf 8 -*-
"""
Define a suite a tests for the utils.
"""
import numpy as np

from welly.utils import moving_average, moving_avg_conv
from welly.utils import top_and_tail, extrapolate
from welly.utils import normalize
from welly.utils import find_nearest
from welly.utils import list_and_add
from welly.utils import dd2dms
from welly.utils import hex_to_rgb, text_colour_for_hex


def test_moving_avg():
    """
    Test basic stuff.
    """
    a = np.array([1, 9, 9, 9, 9, 9, 9, 2, 3, 9, 2, 2, 3, 1, 1, 1, 1, 3, 4, 9, 9, 9, 8, 3])
    m = moving_average(a, 5, mode='same')
    t = [4.2,  5.8,  7.4,  9.0,  9.0,  7.6,  6.4,  6.4,  5.0,  3.6,  3.8,
         3.4,  1.8,  1.6,  1.4,  1.4,  2.0,  3.6,  5.2,  6.8,  7.8,  7.6,
         6.4,  5.2]
    assert len(m) == len(a)
    assert np.allclose(m, t)

    # Heads up, these should not be different.
    t = [3.8,  5.6,  7.4,  9.0,  9.0,  7.6,  6.4,  6.4,  5.0,  3.6,  3.8,
         3.4,  1.8,  1.6,  1.4,  1.4,  2.0,  3.6,  5.2,  6.8,  7.8,  7.6,
         5.8,  4.0]
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
    t = [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.125, 0.25, 1.0, 0.125,  0.125,
         0.25, 0.0, 0.0, 0.0,  0.0, 0.25, 0.375, 1.0, 1.0, 1.0, 0.875, 0.25]
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
