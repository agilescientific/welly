# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Curve module.
"""
import numpy as np

from welly import Synthetic


def test_synthetic():
    """
    Test basic stuff.
    """
    data = np.array([4, 2, 0, -4, -2, 1, 3, 6, 3, 1, -2, -5, -1, 0])
    params = {'dt': 0.004}
    s = Synthetic(data, params=params)

    assert s.dt == 0.004
    assert s.name == 'Synthetic'
