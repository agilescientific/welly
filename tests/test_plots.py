# -*- coding: utf 8 -*-
"""
Defines a suite a tests for images run with:

    py.test --mpl

To generate new test images, see the instructions in
welly/run_tests.py

https://pypi.python.org/pypi/pytest-mpl/0.3
"""
import pytest

from welly import Well
from welly import Synthetic

params = {'tolerance': 20,
          'savefig_kwargs': {'dpi': 100},
          }

FNAME = 'tests/P-129_out.LAS'


@pytest.mark.mpl_image_compare(**params)
def test_curve_plot():
    """
    Tests mpl image of curve.
    """
    well = Well.from_las(FNAME)

    fig = well.data['GR'].plot(return_fig=True)

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_curve_2d_plot():
    """
    Tests mpl image of curve as VD display.
    """
    well = Well.from_las(FNAME)

    fig = well.data['GR'].plot_2d(return_fig=True)

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_synthetic_plot():
    """
    Tests mpl image of synthetic.
    """
    data = [4, 2, 0, -4, -2, 1, 3, 6, 3, 1, -2, -5, -1, 0]
    params = {'dt': 0.004}
    s = Synthetic(data, params=params)

    fig = s.plot(return_fig=True)

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_well_synthetic_plot():
    """
    Tests mpl image of synthetic.
    """
    w = Well.from_las(FNAME)
    w.make_synthetic()

    fig = w.data['Synthetic'].plot(return_fig=True)

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_well_plot():
    """
    Tests mpl image of well.
    """
    well = Well.from_las(FNAME)

    fig = well.plot(tracks=['MD', 'GR', 'DT'],
                    extents='curves',
                    return_fig=True)

    return fig
