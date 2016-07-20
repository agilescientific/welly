# -*- coding: utf 8 -*-
"""
Define a suite a tests for the canstrat functions.
"""
import numpy as np

from striplog import Striplog
from welly import Well


def test_canstrat():
    """
    Test basic stuff.
    """
    w = Well.from_las('tests/P-129_out.LAS')
    s = Striplog.from_csv('tests/K90_strip_pred.csv')
    w.data['test'] = s
    dat = w.to_canstrat(key='test', log='K   90', as_text=True)

    s7 = "K   907   3960 3966L0                                                           "
    assert s7 in dat
