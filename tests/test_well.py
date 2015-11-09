# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Well module.
"""

from welly import Well


def test_well():

    fname = 'tests/P-129_out.LAS'
    well = Well(fname)
    assert well.well.DATE.data == '10-Oct-2007'
    assert well.data['GR'][0] == 46.69865036
