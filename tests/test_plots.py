# -*- coding: utf 8 -*-
"""
Defines a suite a tests for images run with:

    py.test --mpl

To generate new test images, see the instructions in
welly/run_tests.py

https://pypi.python.org/pypi/pytest-mpl/0.3
"""
import pytest
import matplotlib.pyplot as plt

from welly import Well
from welly import Project
from welly import Synthetic
from welly import Location

params = {'tolerance': 20,
          'savefig_kwargs': {'dpi': 100},
          }

FNAME = 'tests/assets/P-129_out.LAS'
FNAME_PROJECT = 'tests/assets/P-129_out-with*.LAS'


@pytest.mark.mpl_image_compare(**params)
def test_project_plot_map():
    """
    Tests mpl image of curve.
    """
    project = Project.from_las(FNAME_PROJECT)

    project[0].location = Location(params={'x': 1000, 'y': 1050})
    project[1].location = Location(params={'x': 1010, 'y': 1060})

    fig = project.plot_map()

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_project_kdes_plot():
    """
    Tests mpl image of curve.
    """
    project = Project.from_las(FNAME)
    project += project

    fig = project.plot_kdes(mnemonic='GR')

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_curve_kde_plot():
    """
    Tests mpl image of curve.
    """
    well = Well.from_las(FNAME)

    fig = well.data['GR'].plot_kde()

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_curve_plot(curve):
    """
    Tests mpl image of curve.
    """
    fig = curve.plot()
    return fig


@pytest.mark.mpl_image_compare(**params)
def test_curve_2d_plot(well):
    """
    Tests mpl image of curve as VD display.
    """
    fig = well.data['GR'].plot_2d()

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_synthetic_plot():
    """
    Tests mpl image of synthetic.
    """
    data = [4, 2, 0, -4, -2, 1, 3, 6, 3, 1, -2, -5, -1, 0]
    params = {'dt': 0.004}
    s = Synthetic(data, params=params)

    fig = s.plot()

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_well_synthetic_plot():
    """
    Tests mpl image of synthetic.
    """
    w = Well.from_las(FNAME)
    w.make_synthetic()

    fig = w.data['Synthetic'].plot()

    return fig


@pytest.mark.mpl_image_compare(**params)
def test_well_plot(well):
    """
    Tests mpl image of well.
    """
    fig = well.plot(tracks=['MD', 'GR', 'DT'],
                    extents='curves')

    return fig
