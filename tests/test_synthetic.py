# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Synthetic class.
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


def test_synthetic_as_curve():
    """
    Test synthetic to curve.
    """
    data = np.array([4, 2, 0, -4, -2, 1, 3, 6, 3, 1, -2, -5, -1, 0])
    params = {'dt': 0.004}
    s = Synthetic(data, params=params)

    crv = s.as_curve(0, 500, 0.1, mnemonic="SYNTH_CRV")

    assert crv.index[0] == 0
    assert round((crv.index[1]-crv.index[0]),2) == 0.1
    assert crv.mnemonic == 'SYNTH_CRV'