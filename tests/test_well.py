# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Well module.
"""
from welly import Well

FNAME = 'tests/P-129_out.LAS'


def test_well():

    well = Well.from_las(FNAME)

    # Check some basics.
    assert well.header.license == 'P-129'
    assert well.location.country == 'CA'
    assert well.location.gl == 90.3
    assert len(well.data) == 25
    assert well.data['GR'][0] - 46.69865036 < 0.001
    assert len(well.survey_basis()) == 12718

    # This is garbled, but it is what it is.
    assert well.uwi == "Long = 63* 45'24.460  W"

    # Check we have the lasio object.
    assert well.las.well['STRT'].value == 1.0668

    # Check we can make one.
    assert well.to_lasio().well['FLD'].value == "Windsor Block"


def test_well_write():
    w = Well.from_las(FNAME)
    w.to_las('tests/test.las')
    well = Well.from_las('tests/test.las')
    assert well.data['GR'][0] - 46.69865036 < 0.001
