# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Location module.
"""
import os
import re

import numpy as np

from welly import Well, Location
from welly import utils

# Some globals.
FNAME = 'tests/assets/P-129_out.LAS'
DNAME = 'tests/assets/P-129_deviation_survey.csv'
DNAME2 = 'tests/assets/Well_1515_directional.csv'


def test_deviation(well):
    """
    Test that we can load a deviation survey and compute position.
    """
    dev = np.loadtxt(DNAME, delimiter=',', skiprows=1)
    well.location.add_deviation(dev)
    assert well.location.position.shape == (46, 3)
    assert well.location.md2tvd(1000) - 998.45378 < 0.001
    assert well.location.tvd2md(998.45378) - 1000 < 0.001
    assert (well.location.dogleg < 1.15).all()


def test_well_remap():
    """
    This is about loading messy data from LAS by renaming and transforming fields.
    """
    def transform_ll(text):
        """
        The transforming function.
        """
        def callback(match):
            d = match.group(1).strip()
            m = match.group(2).strip()
            s = match.group(3).strip()
            c = match.group(4).strip()
            if c.lower() in ('w', 's') and d[0] != '-':
                d = '-' + d
            return ' '.join([d, m, s])

        regex = r".+?([-0-9]+?).? ?([0-9]+?).? ?([\.0-9]+?).? +?([NESW])"
        pattern = re.compile(regex, re.I)
        text = pattern.sub(callback, text)
        return utils.dms2dd([float(i) for i in text.split()])

    remap = {
        'LATI': 'LOC',  # Use LOC for the parameter LATI.
        'LONG': 'UWI',  # Use UWI for the parameter LONG.
        'SECT': None,   # Use nothing for the parameter SECT.
        'RANG': None,   # Use nothing for the parameter RANG.
        'TOWN': None,   # Use nothing for the parameter TOWN.
    }

    funcs = {
        'LATI': transform_ll,  # Pass LATI through this function before load.
        'LONG': transform_ll,  # Pass LONG through it too.
        'UWI': lambda x: "No name, oh no!"
    }

    well = Well.from_las(FNAME, remap=remap, funcs=funcs)

    # Check some basics.
    assert (well.location.latitude - 45.20951027) < 0.001
    assert well.uwi == 'No name, oh no!'

    # Check CRS
    well.location.crs_from_epsg(4269)
    assert well.location.crs.data['no_defs']
    assert well.location.crs.to_string() == '+init=epsg:4269 +no_defs'

    well.location.crs_from_string('+init=epsg:4267')
    assert well.location.crs.init == 'epsg:4267'


def test_deviation_to_position_conversion():
    """
    Test that we can convert a deviation survey – a N x 3 array with columns MD, INC, and AZI
    and compute position (a.k.a path) – a N x 3 arry with columns X, Y, Z relative
    to the KB location. Tests the minimum curvature method only.
    """
    location = {'x': 382769.09, 'y': 4994021.65, 'kb': 94.8}
    well = Well({'location': Location(params=location)})

    survey = np.loadtxt(DNAME2, skiprows=2, delimiter=',')
    dev_surv = survey[:, 2:5]  # MD, Incl, Azim columns in test file
    posx, posy, posz = survey[:, 8], survey[:, 7], survey[:, 5]  # E/W, N/S, Z
    well.location.add_deviation(dev_surv)

    assert well.location.trajectory().shape == (1000, 3)
    assert well.location.position.shape == (83, 3)
    assert well.location.position.shape == (83, 3)
    assert (np.allclose(posx, well.location.position[:, 0], atol=0.1))
    assert (np.allclose(posy, well.location.position[:, 1], atol=0.1))


def test_empty_location_td(well):
    well.to_las("temporary.las")

    new_well = Well.from_las("temporary.las")
    new_well.plot()

    assert new_well.location.td is None
    os.remove("temporary.las")


def test_string_location_td():
    FNAME = 'tests/assets/P-129_out-with-string-td.LAS'
    well = Well.from_las(FNAME)
    well.to_las("temporary.las")

    new_well = Well.from_las("temporary.las")
    new_well.plot()

    assert new_well.location.td is None
    os.remove("temporary.las")


def test_numerical_location_td():
    FNAME = 'tests/assets/P-129_out-with-numeric-td.LAS'
    well = Well.from_las(FNAME)
    well.to_las("temporary.las")

    new_well = Well.from_las("temporary.las")
    new_well.plot()

    assert well.location.td == 1935.0
    os.remove("temporary.las")
