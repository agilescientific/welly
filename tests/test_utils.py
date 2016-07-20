# -*- coding: utf 8 -*-
"""
Define a suite a tests for the utils.
"""
import numpy as np

from welly.utils import moving_average, moving_avg_conv
from welly.utils import top_and_tail, extrapolate
from welly.utils import dd2dms


def test_moving_avg():
    """
    Test basic stuff.
    """
    a = np.array([1,9,9,9,9,9,9,2,3,9,2,2,3,1,1,1,1,3,4,9,9,9,8,3])
    m = moving_average(a, 7, mode='same') 
    t = [ 4.4285714, 5.571428, 6.7142857, 7.8571428, 8.,         7.1428571,
          7.1428571, 6.142857, 5.1428571, 4.2857142, 3.1428571,  3.,
          2.7142857, 1.571428, 1.7142857, 2.,        2.8571420,  4.,
          5.1428571, 6.142857, 6.4285714, 6.1428571, 5.7142857,  4.5714285
          ]
    assert len(m) == len(a)
    assert np.allclose(m, t)

    c = moving_avg_conv(a, 7)
    assert np.allclose(c, t)


def test_moving_avg():
    """
    Test basic stuff.
    """
    a = np.array([np.nan,np.nan,9,9,9,9,9,2,3,9,2,1,1,3,4,9,9,9,np.nan,np.nan])
    m = top_and_tail(a)[0]
    t = np.array([9,9,9,9,9,2,3,9,2,1,1,3,4,9,9,9])
    assert len(a) - 4 == len(m)
    assert np.allclose(m, t)


def test_moving_avg():
    """
    Test basic stuff.
    """
    a = np.array([np.nan,np.nan,9,9,9,9,9,2,3,9,2,1,1,3,4,9,9,9,np.nan,np.nan])
    m = extrapolate(a)
    t = np.array([9,9,9,9,9,9,9,2,3,9,2,1,1,3,4,9,9,9,9,9])
    assert len(a) == len(m)
    assert np.allclose(m, t)


def test_dd2dms():
    dms = dd2dms(123.123)
    assert np.allclose(dms, (123, 7, 22.8))
