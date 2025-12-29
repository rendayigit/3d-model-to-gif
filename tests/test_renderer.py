"""
Tests for the renderer module.
"""

import math

import numpy as np
import pytest

from src.renderer import (
    CameraSettings,
    GifSettings,
    ImageSettings,
    LightingPreset,
    create_rotation_matrix,
)


class TestCameraSettings:
    """Tests for CameraSettings dataclass."""

    def test_default_values(self):
        """Test default camera settings."""
        camera = CameraSettings()
        assert camera.zoom == 2.0
        assert camera.offset_x == 0.0
        assert camera.offset_y == 0.0

    def test_custom_values(self):
        """Test custom camera settings."""
        camera = CameraSettings(zoom=5.0, offset_x=1.0, offset_y=-1.0)
        assert camera.zoom == 5.0
        assert camera.offset_x == 1.0
        assert camera.offset_y == -1.0

    def test_pose_matrix_shape(self):
        """Test that pose matrix has correct shape."""
        camera = CameraSettings()
        matrix = camera.get_pose_matrix()
        assert matrix.shape == (4, 4)

    def test_pose_matrix_values(self):
        """Test pose matrix contains correct values."""
        camera = CameraSettings(zoom=3.0, offset_x=1.0, offset_y=2.0)
        matrix = camera.get_pose_matrix()
        assert matrix[0, 3] == 1.0  # offset_x
        assert matrix[1, 3] == 2.0  # offset_y
        assert matrix[2, 3] == 3.0  # zoom


class TestLightingPreset:
    """Tests for LightingPreset dataclass."""

    def test_preset_creation(self):
        """Test creating a lighting preset."""
        preset = LightingPreset("Test", 5.0, (1.0, 0.9, 0.8))
        assert preset.name == "Test"
        assert preset.intensity == 5.0
        assert preset.color == (1.0, 0.9, 0.8)

    def test_get_presets(self):
        """Test that all presets are available."""
        presets = LightingPreset.get_presets()
        expected_keys = ["default", "warm", "cool", "bright", "dim", "dramatic"]
        for key in expected_keys:
            assert key in presets
            assert isinstance(presets[key], LightingPreset)

    def test_preset_values(self):
        """Test specific preset values."""
        presets = LightingPreset.get_presets()

        default = presets["default"]
        assert default.intensity == 5.0
        assert default.color == (1.0, 1.0, 1.0)

        warm = presets["warm"]
        assert warm.color[0] > warm.color[2]  # Red > Blue for warm


class TestGifSettings:
    """Tests for GifSettings dataclass."""

    def test_default_values(self):
        """Test default GIF settings."""
        settings = GifSettings()
        assert settings.duration == 4.0
        assert settings.fps == 15
        assert settings.rotate_speed == 90.0
        assert settings.lighting_intensity == 5.0

    def test_custom_values(self):
        """Test custom GIF settings."""
        settings = GifSettings(duration=6.0, fps=30, rotate_speed=120.0, lighting_intensity=8.0)
        assert settings.duration == 6.0
        assert settings.fps == 30
        assert settings.rotate_speed == 120.0
        assert settings.lighting_intensity == 8.0


class TestImageSettings:
    """Tests for ImageSettings dataclass."""

    def test_default_values(self):
        """Test default image settings."""
        settings = ImageSettings()
        assert settings.width == 800
        assert settings.height == 800
        assert len(settings.angles) == 8
        assert 0 in settings.angles
        assert 180 in settings.angles

    def test_custom_values(self):
        """Test custom image settings."""
        settings = ImageSettings(width=1920, height=1080, angles=[0, 90, 180, 270])
        assert settings.width == 1920
        assert settings.height == 1080
        assert settings.angles == [0, 90, 180, 270]


class TestRotationMatrix:
    """Tests for rotation matrix creation."""

    def test_y_axis_rotation_shape(self):
        """Test Y-axis rotation matrix shape."""
        matrix = create_rotation_matrix(90, "y")
        assert matrix.shape == (4, 4)

    def test_identity_at_zero(self):
        """Test that 0 degree rotation is identity-like."""
        matrix = create_rotation_matrix(0, "y")
        expected = np.eye(4)
        np.testing.assert_array_almost_equal(matrix, expected)

    def test_90_degree_rotation(self):
        """Test 90 degree Y-axis rotation."""
        matrix = create_rotation_matrix(90, "y")
        # After 90 degree Y rotation, X axis should point to -Z
        assert abs(matrix[0, 0]) < 1e-10  # cos(90) ≈ 0
        assert abs(matrix[0, 2] - 1.0) < 1e-10  # sin(90) = 1

    def test_x_axis_rotation(self):
        """Test X-axis rotation matrix."""
        matrix = create_rotation_matrix(90, "x")
        assert matrix.shape == (4, 4)
        # X component should be unchanged
        assert matrix[0, 0] == 1.0

    def test_z_axis_rotation(self):
        """Test Z-axis rotation matrix."""
        matrix = create_rotation_matrix(90, "z")
        assert matrix.shape == (4, 4)
        # Z component should be unchanged
        assert matrix[2, 2] == 1.0

    def test_invalid_axis(self):
        """Test invalid axis returns identity."""
        matrix = create_rotation_matrix(90, "invalid")
        expected = np.eye(4)
        np.testing.assert_array_equal(matrix, expected)

    def test_full_rotation(self):
        """Test 360 degree rotation returns to identity."""
        matrix = create_rotation_matrix(360, "y")
        expected = np.eye(4)
        np.testing.assert_array_almost_equal(matrix, expected)
