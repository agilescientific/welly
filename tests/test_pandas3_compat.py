# -*- coding: utf-8 -*-
"""
Test suite for pandas 3.0 compatibility.

These tests verify that welly works correctly with pandas 3.0's:
- New string dtype (str instead of object)
- Copy-on-Write (CoW) behavior
- Removed deprecated functionality
"""
import os
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

from welly import Well, Curve, Project
from welly.las import from_las


class TestStringDtypeCompatibility:
    """Tests for pandas 3.0 string dtype changes."""

    def test_las_string_null_handling(self):
        """Test that string null values are properly replaced."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        # Should not raise any errors
        df = well.df()
        assert df is not None
        assert len(df) > 0

    def test_object_to_numeric_conversion(self):
        """Test conversion of string numbers to numeric."""
        df = pd.DataFrame({
            'DEPT': [1.0, 2.0, 3.0],
            'GR': ['10.5', '20.3', '30.1'],
            'LITH': ['sand', 'shale', 'sand']
        })
        well = Well.from_df(df)
        result = well.df()

        # GR should be numeric
        assert pd.api.types.is_numeric_dtype(result['GR'])
        # LITH should remain non-numeric
        assert not pd.api.types.is_numeric_dtype(result['LITH'])

    def test_select_dtypes_with_string(self):
        """Test select_dtypes works with new string dtype."""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['x', 'y', 'z'],
            'C': [1.1, 2.2, 3.3]
        })

        # Should work regardless of whether B is 'object' or 'string'
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        assert 'A' in numeric_cols
        assert 'C' in numeric_cols
        assert 'B' not in numeric_cols

    def test_curve_as_numpy_numeric_only(self):
        """Test as_numpy returns only numeric data."""
        c = Curve(data=np.linspace(1, 100, 50))
        arr = c.as_numpy()
        assert isinstance(arr, np.ndarray)
        assert arr.dtype in [np.float64, np.float32, np.int64, np.int32]

    def test_mixed_dtype_dataframe(self):
        """Test handling of DataFrames with mixed dtypes."""
        df = pd.DataFrame({
            'DEPT': [1.0, 2.0, 3.0],
            'GR': [10.5, 20.3, 30.1],
            'FACIES': ['A', 'B', 'A'],
            'FLAG': [True, False, True]
        })
        well = Well.from_df(df)
        result = well.df()

        assert pd.api.types.is_numeric_dtype(result['GR'])
        assert pd.api.types.is_numeric_dtype(result['DEPT'])


class TestCopyOnWriteCompatibility:
    """Tests for pandas 3.0 Copy-on-Write behavior."""

    def test_well_df_modification(self):
        """Test that well.df() returns independent copy."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        df1 = well.df()
        df2 = well.df()

        # Modifying df1 should not affect df2
        if len(df1) > 0:
            original_value = df2.iloc[0, 0]
            df1.iloc[0, 0] = -9999
            assert df2.iloc[0, 0] == original_value

    def test_inplace_operations_no_warnings(self):
        """Test that operations don't produce CoW warnings."""
        well = Well.from_las('tests/assets/P-129_out.LAS')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df = well.df(uwi=True)

            # Filter for pandas FutureWarnings about CoW
            cow_warnings = [
                x for x in w
                if issubclass(x.category, FutureWarning)
                and 'copy' in str(x.message).lower()
            ]
            assert len(cow_warnings) == 0, f"Got CoW warnings: {cow_warnings}"

    def test_las_roundtrip_no_warnings(self):
        """Test LAS read/write cycle produces no CoW warnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            well = Well.from_las('tests/assets/P-129_out.LAS')

            with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as f:
                temp_path = f.name

            try:
                well.to_las(temp_path)
                well2 = Well.from_las(temp_path)
                assert well2 is not None
            finally:
                os.unlink(temp_path)

            # Check for CoW-related warnings
            cow_warnings = [
                x for x in w
                if 'copy' in str(x.message).lower()
                and issubclass(x.category, (FutureWarning, DeprecationWarning))
            ]
            assert len(cow_warnings) == 0, f"Got warnings: {cow_warnings}"

    def test_curve_operations_no_mutation(self):
        """Test that curve operations don't mutate original."""
        c1 = Curve(data=np.linspace(1, 100, 50))
        original_first = c1.df.iloc[0, 0]

        c2 = c1 + 100
        # Original should be unchanged
        assert c1.df.iloc[0, 0] == original_first
        # New curve should have modified values
        assert c2.df.iloc[0, 0] == original_first + 100


class TestDataFrameOperations:
    """Tests for DataFrame operations compatibility."""

    def test_concat_operations(self):
        """Test pd.concat works correctly."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        df = well.df()

        # Should produce valid DataFrame
        assert isinstance(df, pd.DataFrame)
        assert len(df.columns) > 0

    def test_multiindex_operations(self):
        """Test MultiIndex operations work correctly."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        df = well.df(uwi=True)

        # Should have MultiIndex
        assert isinstance(df.index, pd.MultiIndex)
        assert df.index.nlevels == 2

    def test_dataframe_from_curves(self):
        """Test creating DataFrame from multiple curves."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        keys = list(well.data.keys())[:3]  # First 3 curves
        df = well.df(keys=keys)

        assert len(df.columns) == len(keys)
        assert all(col in df.columns for col in keys)


class TestCurveOperations:
    """Tests for Curve operations with pandas 3.0."""

    def test_curve_step_property(self):
        """Test step property works with numeric index."""
        c = Curve(data=np.linspace(1, 100, 50), index=np.arange(50))
        step = c.step
        assert step is not None
        assert isinstance(step, (int, float, np.integer, np.floating))

    def test_curve_categorical(self):
        """Test categorical curve handling."""
        data = ['sand'] * 10 + ['shale'] * 10
        c = Curve(data=data, dtype='category')
        assert c.df.dtypes[0] == 'category'

    def test_curve_block_operation(self):
        """Test curve blocking works correctly."""
        c = Curve(data=np.linspace(0, 100, 100))
        blocked = c.block(cutoffs=[30, 70])

        assert blocked is not None
        assert len(blocked) == len(c)
        assert blocked.df.max()[0] == 2  # 3 blocks: 0, 1, 2

    def test_curve_to_basis(self):
        """Test curve resampling to new basis."""
        c = Curve(data=np.linspace(1, 100, 100), index=np.arange(100))
        c_new = c.to_basis(start=10, stop=50, step=2)

        assert c_new is not None
        assert len(c_new) == 21  # (50-10)/2 + 1

    def test_curve_arithmetic(self):
        """Test curve arithmetic operations."""
        c1 = Curve(data=np.array([1.0, 2.0, 3.0]))
        c2 = Curve(data=np.array([10.0, 20.0, 30.0]))

        # Addition
        c_add = c1 + c2
        np.testing.assert_array_almost_equal(
            c_add.values, [11.0, 22.0, 33.0]
        )

        # Multiplication
        c_mul = c1 * 2
        np.testing.assert_array_almost_equal(
            c_mul.values, [2.0, 4.0, 6.0]
        )


class TestLASOperations:
    """Tests for LAS file operations."""

    def test_from_las_datasets(self):
        """Test from_las returns proper datasets structure."""
        datasets = from_las('tests/assets/P-129_out.LAS')

        assert 'Header' in datasets
        assert isinstance(datasets['Header'], pd.DataFrame)

    def test_las_header_parsing(self):
        """Test LAS header is parsed correctly."""
        well = Well.from_las('tests/assets/P-129_out.LAS')

        assert well.header is not None
        assert isinstance(well.header, pd.DataFrame)
        assert 'mnemonic' in well.header.columns

    def test_las_write_read_roundtrip(self):
        """Test writing and reading LAS preserves data."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        original_gr = well.data['GR'].values.copy()

        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as f:
            temp_path = f.name

        try:
            well.to_las(temp_path)
            well2 = Well.from_las(temp_path)

            np.testing.assert_array_almost_equal(
                well2.data['GR'].values,
                original_gr,
                decimal=4
            )
        finally:
            os.unlink(temp_path)


class TestProjectOperations:
    """Tests for Project operations with pandas 3.0."""

    def test_project_creation(self):
        """Test Project can be created from wells."""
        well1 = Well.from_las('tests/assets/P-129_out.LAS')
        well2 = Well.from_las('tests/assets/1.las')

        project = Project([well1, well2])
        assert len(project) == 2

    def test_project_df(self):
        """Test Project.df() works correctly."""
        well1 = Well.from_las('tests/assets/P-129_out.LAS')

        project = Project([well1])
        df = project.df()

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_project_iteration(self):
        """Test iterating over Project wells."""
        well1 = Well.from_las('tests/assets/P-129_out.LAS')
        project = Project([well1])

        wells = list(project)
        assert len(wells) == 1
        assert isinstance(wells[0], Well)


# Parametrized tests for multiple LAS files
@pytest.mark.parametrize("las_file", [
    'tests/assets/1.las',
    'tests/assets/2.las',
    'tests/assets/P-129_out.LAS',
    'tests/assets/F03-02.las',
])
def test_las_file_loading(las_file):
    """Test loading various LAS files works without errors."""
    well = Well.from_las(las_file)
    assert well is not None
    assert len(well.data) > 0


@pytest.mark.parametrize("las_file", [
    'tests/assets/P-129_out.LAS',
    'tests/assets/1.las',
])
def test_las_roundtrip(las_file):
    """Test LAS read/write roundtrip preserves data."""
    well = Well.from_las(las_file)
    original_curves = list(well.data.keys())

    with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as f:
        temp_path = f.name

    try:
        well.to_las(temp_path)
        well2 = Well.from_las(temp_path)

        # Check at least some curves are preserved
        common_curves = set(original_curves) & set(well2.data.keys())
        assert len(common_curves) > 0

        for curve in common_curves:
            if curve in well2.data and curve in well.data:
                np.testing.assert_array_almost_equal(
                    well.data[curve].values,
                    well2.data[curve].values,
                    decimal=4
                )
    finally:
        os.unlink(temp_path)


@pytest.mark.parametrize("dtype", ['float64', 'int64', 'category'])
def test_curve_dtype_handling(dtype):
    """Test curves handle different dtypes correctly."""
    if dtype == 'category':
        data = ['A', 'B', 'C'] * 10
    else:
        data = np.arange(30, dtype=dtype)

    c = Curve(data=data, dtype=dtype if dtype == 'category' else None)
    assert c is not None
    assert len(c) == 30
