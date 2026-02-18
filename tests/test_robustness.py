"""
Tests for Phase 2 robustness improvements.

Tests cover:
- 2.1: well.df() auto-interpolation for different curve bases
- 2.2: curve.block() with string labels
- 2.3: to_las() key validation
"""
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

from welly import Well, Curve
from welly.well import WellError


class TestWellDfBasisHandling:
    """Tests for Phase 2.1 - well.df() basis handling improvements."""

    def test_df_with_common_basis(self):
        """Test that df() works normally when curves share a common basis."""
        # Create curves with same basis
        basis = np.arange(0, 100, 0.5)
        curve1 = Curve(data=np.random.rand(len(basis)), index=basis, mnemonic='GR')
        curve2 = Curve(data=np.random.rand(len(basis)), index=basis, mnemonic='RHOB')
        
        well = Well({'data': {'GR': curve1, 'RHOB': curve2}})
        df = well.df()
        
        assert df.shape[1] == 2
        assert 'GR' in df.columns
        assert 'RHOB' in df.columns

    def test_df_with_overlapping_bases(self):
        """Test that df() works when curves have overlapping but different bases."""
        # Create curves with overlapping bases - survey_basis should find common ground
        basis1 = np.arange(0, 100, 0.5)
        basis2 = np.arange(50, 150, 0.5)  # Overlapping range
        
        curve1 = Curve(data=np.random.rand(len(basis1)), index=basis1, mnemonic='GR')
        curve2 = Curve(data=np.random.rand(len(basis2)), index=basis2, mnemonic='RHOB')
        
        well = Well({'data': {'GR': curve1, 'RHOB': curve2}})
        
        # Should work - survey_basis finds common basis from overlapping ranges
        df = well.df()
        
        assert df.shape[1] == 2
        assert 'GR' in df.columns
        assert 'RHOB' in df.columns

    def test_df_with_explicit_basis(self):
        """Test that df() uses explicit basis when provided."""
        basis1 = np.arange(0, 100, 0.5)
        basis2 = np.arange(50, 150, 0.5)
        
        curve1 = Curve(data=np.random.rand(len(basis1)), index=basis1, mnemonic='GR')
        curve2 = Curve(data=np.random.rand(len(basis2)), index=basis2, mnemonic='RHOB')
        
        well = Well({'data': {'GR': curve1, 'RHOB': curve2}})
        
        # Provide explicit basis
        explicit_basis = np.arange(25, 125, 1.0)
        df = well.df(basis=explicit_basis)
        
        assert len(df) == len(explicit_basis)
        np.testing.assert_array_almost_equal(df.index.values, explicit_basis)

    def test_compute_union_basis(self):
        """Test the _compute_union_basis helper method."""
        basis1 = np.arange(0, 50, 0.5)
        basis2 = np.arange(30, 100, 0.5)
        
        curve1 = Curve(data=np.random.rand(len(basis1)), index=basis1, mnemonic='GR')
        curve2 = Curve(data=np.random.rand(len(basis2)), index=basis2, mnemonic='RHOB')
        
        well = Well({'data': {'GR': curve1, 'RHOB': curve2}})
        
        union_basis = well._compute_union_basis()
        
        # Should span from min start to max stop
        assert union_basis[0] == 0
        assert union_basis[-1] >= 99  # Close to 100

    def test_compute_union_basis_with_no_overlap(self):
        """Test _compute_union_basis with non-overlapping curves."""
        basis1 = np.arange(0, 50, 0.5)
        basis2 = np.arange(100, 150, 0.5)  # No overlap
        
        curve1 = Curve(data=np.random.rand(len(basis1)), index=basis1, mnemonic='GR')
        curve2 = Curve(data=np.random.rand(len(basis2)), index=basis2, mnemonic='RHOB')
        
        well = Well({'data': {'GR': curve1, 'RHOB': curve2}})
        
        union_basis = well._compute_union_basis()
        
        # Should span from 0 to ~150
        assert union_basis[0] == 0
        assert union_basis[-1] >= 149

    def test_df_auto_interpolate_parameter(self):
        """Test that auto_interpolate parameter is accepted."""
        basis = np.arange(0, 100, 0.5)
        curve1 = Curve(data=np.random.rand(len(basis)), index=basis, mnemonic='GR')
        
        well = Well({'data': {'GR': curve1}})
        
        # Both should work
        df1 = well.df(auto_interpolate=True)
        df2 = well.df(auto_interpolate=False)
        
        assert df1.shape == df2.shape


class TestCurveBlockLabels:
    """Tests for Phase 2.2 - curve.block() with string labels."""

    def test_block_with_labels(self):
        """Test that block() stores labels when provided."""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        curve = Curve(data=data, mnemonic='GR')
        
        blocked = curve.block(cutoffs=[30, 70], labels=['Low', 'Medium', 'High'])
        
        assert hasattr(blocked, 'block_labels')
        assert blocked.block_labels == {0: 'Low', 1: 'Medium', 2: 'High'}

    def test_block_without_labels(self):
        """Test that block() works without labels (backward compatible)."""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        curve = Curve(data=data, mnemonic='GR')
        
        blocked = curve.block(cutoffs=[30, 70])
        
        # Should not have block_labels attribute
        assert not hasattr(blocked, 'block_labels')

    def test_block_labels_warning_on_mismatch(self):
        """Test that block() warns when label count doesn't match cutoffs."""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        curve = Curve(data=data, mnemonic='GR')
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # 2 cutoffs need 3 labels, but we provide 2
            blocked = curve.block(cutoffs=[30, 70], labels=['Low', 'High'])
            assert any("Expected 3 labels" in str(warning.message) for warning in w)

    def test_block_labels_with_integer_values(self):
        """Test that block() stores labels when integer values are provided."""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        curve = Curve(data=data, mnemonic='GR')
        
        # Use integer values to avoid dtype issues
        blocked = curve.block(
            cutoffs=[30, 70],
            values=[1, 2, 3],
            labels=['Low', 'Medium', 'High']
        )
        
        assert hasattr(blocked, 'block_labels')
        assert blocked.block_labels[0] == 'Low'

    def test_block_labels_single_cutoff(self):
        """Test block() with a single cutoff and labels."""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        curve = Curve(data=data, mnemonic='GR')
        
        blocked = curve.block(cutoffs=[50], labels=['Below', 'Above'])
        
        assert hasattr(blocked, 'block_labels')
        assert blocked.block_labels == {0: 'Below', 1: 'Above'}


class TestToLasRobustness:
    """Tests for Phase 2.3 - to_las() key validation."""

    def test_to_las_with_valid_keys(self):
        """Test that to_las() works with valid keys."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        
        # Get actual curve names from the well
        available_keys = list(well.data.keys())[:2]
        
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as f:
            temp_path = f.name
        
        # Should work without issues
        well.to_las(temp_path, keys=available_keys)
        
        # Verify file was created
        well2 = Well.from_las(temp_path)
        for key in available_keys:
            assert key in well2.data

    def test_to_las_with_all_invalid_keys_error(self):
        """Test that to_las() raises error when all keys are invalid."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as f:
            temp_path = f.name
        
        # Should raise error when no valid keys
        with pytest.raises(WellError):
            well.to_las(temp_path, keys=['FAKE1', 'FAKE2'])

    def test_to_lasio_with_valid_keys(self):
        """Test that to_lasio() works with valid keys."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        
        # Get actual curve names
        available_keys = list(well.data.keys())[:2]
        
        las = well.to_lasio(keys=available_keys)
        
        # Should have the requested curves
        curve_names = [c.mnemonic for c in las.curves]
        for key in available_keys:
            assert key in curve_names

    def test_to_lasio_with_all_invalid_keys_error(self):
        """Test that to_lasio() raises error when all keys are invalid."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        
        with pytest.raises(WellError):
            well.to_lasio(keys=['FAKE1', 'FAKE2'])


class TestIntegration:
    """Integration tests combining multiple Phase 2 features."""

    def test_block_and_export_workflow(self):
        """Test blocking a curve and exporting to LAS."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        
        # Get a curve and block it
        gr_key = 'GR'
        if gr_key in well.data:
            blocked_gr = well.data[gr_key].block(
                cutoffs=[50, 100],
                labels=['Low GR', 'Medium GR', 'High GR']
            )
            # Set a unique mnemonic for the blocked curve
            blocked_gr.mnemonic = 'GR_BLOCKED'
            well.data['GR_BLOCKED'] = blocked_gr
            
            assert hasattr(well.data['GR_BLOCKED'], 'block_labels')
            
            # Export to LAS
            with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as f:
                temp_path = f.name
            
            well.to_las(temp_path, keys=[gr_key, 'GR_BLOCKED'])
            
            # Read back and verify
            well2 = Well.from_las(temp_path)
            assert gr_key in well2.data
            assert 'GR_BLOCKED' in well2.data

    def test_df_with_subset_of_curves(self):
        """Test df() with a subset of curves."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        
        # Get first two curves
        keys = list(well.data.keys())[:2]
        
        df = well.df(keys=keys)
        
        assert df.shape[1] == len(keys)
        for key in keys:
            assert key in df.columns

    def test_compute_union_basis_method_exists(self):
        """Test that _compute_union_basis method exists and is callable."""
        well = Well.from_las('tests/assets/P-129_out.LAS')
        
        assert hasattr(well, '_compute_union_basis')
        assert callable(well._compute_union_basis)
        
        # Should return a basis
        basis = well._compute_union_basis()
        assert basis is not None
        assert len(basis) > 0
