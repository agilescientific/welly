# -*- coding: utf 8 -*-
"""
Defines a suite a tests for images run with:

    py.test --mpl

To generate new test images, see the instructions in
welly/run_tests.py

https://pypi.python.org/pypi/pytest-mpl/0.3
"""
from welly import Well

import pytest

params = {'tolerance': 20,
          'savefig_kwargs': {'dpi': 100},
          }

FNAME = 'tests/P-129_out.LAS'


@pytest.mark.mpl_image_compare(**params)
def test_curve_plot():
    """
    Tests mpl image of striplog.
    """
    well = Well.from_las(FNAME)

    fig = well.data['GR'].plot(return_fig=True)

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_well_plot():
    """
    Tests mpl image of striplog.
    """
    well = Well.from_las(FNAME)

    fig = well.plot(tracks=['MD', 'GR', 'DT'], return_fig=True)

    return fig
