from pytest import fixture
import numpy as np
import pandas as pd

from welly import Project


@fixture()
def project():
    return Project.from_las('tests/assets/P-129_out.LAS')


@fixture()
def well(project):
    return project[0]


@fixture()
def curve(well):
    return well.data['GR']


@fixture()
def df():
    return pd.DataFrame({'GR': [80, 100, 90], 'DEN': [1.5, 1.2, np.nan]}, index=[100, 150, 200])
