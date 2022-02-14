# -*- coding: utf 8 -*-
"""
Define a suite a tests for the canstrat functions.
"""
from striplog import Striplog


def test_canstrat(well):
    """
    Test conversion of well to canstrat.
    """
    s = Striplog.from_csv('tests/assets/K90_strip_pred.csv')
    well.data['test'] = s
    dat = well.to_canstrat(key='test',
                           log='K   90',
                           lith_field="component",
                           as_text=True
                           )

    s7 = "K   907   3960 3966L0                                                           "
    assert s7 in dat
