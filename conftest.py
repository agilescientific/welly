"""
Pytest fixtures that are available to all test modules upon runtime.
"""
from pytest import fixture
import numpy as np
import pandas as pd

from welly import Project


@fixture()
def project():
    """ A Project loaded from LAS """
    return Project.from_las('tests/assets/P-129_out.LAS')


@fixture()
def well(project):
    """ A Well subsetted from the loaded Project object "" """
    return project[0]


@fixture()
def curve(well):
    """ A Curve subsetted from the subsetted Well object """
    return well.data['GR']


@fixture()
def df():
    """ A pd.DataFrame with curve data and an index """
    return pd.DataFrame({'GR': [80, 100, 90], 'DEN': [1.5, 1.2, np.nan]}, index=[100, 150, 200])
