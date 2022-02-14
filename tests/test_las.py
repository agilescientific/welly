# -*- coding: utf 8 -*-
"""
Define a suite a tests for the welly.las reader/writer module.
"""

import os
import shutil

from lasio import read
from pandas.testing import assert_frame_equal

from welly.las import datasets_to_las, from_las

paths_in = [
    'tests/assets/1.las',
    'tests/assets/2.las',
    'tests/assets/F03-02.las',
    'tests/assets/P-129_out-with-numeric-td.LAS',
    'tests/assets/P-129_out-with-string-td.LAS',
    'tests/assets/P-129_out.LAS'
]

# create temporary directory write las files to disk with welly.to_las()
dir_temp = 'tests/temp'
if os.path.exists(dir_temp):
    shutil.rmtree(dir_temp)
    os.mkdir(dir_temp)
else:
    os.mkdir(dir_temp)

# define temporary export path for every las file in paths_in
paths_out = [os.path.join(dir_temp, 'temp{}.las').format(i) for i in range(len(paths_in))]


def test_from_and_to_las():
    """
    Test the welly.from_las() reader and welly.to_las() writer function.

    welly.from_las():
        Reads the LAS files with lasio.read() and then parses and returns them
        as two pd.DataFrames (data and header) for every dataset.

    welly.to_las():
        The in-memory object representations of the las files are written to
        disk as .las files.
    """
    # read and parse las files to the dataframe in-memory format
    datasets_parsed_from_las_disk = [from_las(path) for path in paths_in]

    # write in-memory las temporarily to disk
    for i, datasets in enumerate(datasets_parsed_from_las_disk):
        datasets_to_las(paths_out[i], datasets)


def test_to_las():
    """
    Test if the las files that were written to disk from the parsed dataframe
    in-memory objects return the same lasio.LASFile objects as if they were
    directly read with lasio.read(). We do this by reading back the to disk
    written .las files with lasio.read() and comparing them with the
    'untouched' las files that we directly read back with lasio.read().

    This test function fails if test_from_and_to_las() failed because we
    require the .las files that were written to disk.
    """
    # read untouched las files to lasio.LASFile instances for comparison later
    las_originals = [read(path) for path in paths_in]

    # read back written las files from disk to LASFile instances
    las_exported = [read(path) for path in paths_out]

    # untouched las should be equal to those of written las
    for las_original, las_export in zip(las_originals, las_exported):
        assert_frame_equal(las_original.df(), las_export.df(), check_names=False)
        assert las_original.version.VERS.value == las_export.version.VERS.value
        assert las_original.sections['Well'] == las_export.sections['Well']
        assert las_original.sections['Parameter'] == las_export.sections['Parameter']
        assert las_original.sections['Curves'] == las_export.sections['Curves']
        assert las_original.sections['Other'] == las_export.sections['Other']

    # delete the temporary directory where the temporary las files are stored
    shutil.rmtree(dir_temp)
