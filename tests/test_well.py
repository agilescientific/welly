# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Well module.
"""

from welly import Well


def test_well():

    fname = 'tests/P-129_out.LAS'
    well = Well.from_las(fname)
    assert well.data['GR'][0] == 46.69865036
