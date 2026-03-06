"""Tests for bearing capacity module."""

import pytest

from insoiltool.bearing_capacity import BearingCapacity, FoundationShape


@pytest.fixture
def bc():
    return BearingCapacity()


class TestTerzaghi:
    def test_cohesive_soil_strip(self, bc):
        """Pure cohesion (phi=0) strip footing — known reference check."""
        result = bc.terzaghi(
            cohesion=50,
            unit_weight=18,
            depth=1.0,
            width=2.0,
            phi_deg=0,
            shape=FoundationShape.STRIP,
        )
        # qu = c * Nc(=5.7) + q * 1.0; q = 18*1 = 18
        expected_qu = 50 * 5.7 * 1.0 + 18 * 1.0 * 1.0
        assert result.ultimate_bearing_capacity == pytest.approx(expected_qu, rel=0.01)
        assert result.allowable_bearing_capacity == pytest.approx(expected_qu / 3.0, rel=0.01)

    def test_square_footing(self, bc):
        result = bc.terzaghi(
            cohesion=20,
            unit_weight=19,
            depth=1.5,
            width=1.5,
            phi_deg=30,
            shape=FoundationShape.SQUARE,
        )
        assert result.ultimate_bearing_capacity > 0
        assert result.allowable_bearing_capacity == pytest.approx(
            result.ultimate_bearing_capacity / 3.0, rel=1e-6
        )

    def test_custom_factor_of_safety(self, bc):
        result = bc.terzaghi(
            cohesion=10,
            unit_weight=18,
            depth=1.0,
            width=2.0,
            phi_deg=25,
            factor_of_safety=2.5,
        )
        assert result.factor_of_safety == 2.5
        assert result.allowable_bearing_capacity == pytest.approx(
            result.ultimate_bearing_capacity / 2.5, rel=1e-6
        )

    def test_rectangular_requires_length(self, bc):
        with pytest.raises(ValueError, match="Length must be provided"):
            bc.terzaghi(
                cohesion=10,
                unit_weight=18,
                depth=1.0,
                width=2.0,
                phi_deg=25,
                shape=FoundationShape.RECTANGULAR,
            )

    def test_rectangular_with_length(self, bc):
        result = bc.terzaghi(
            cohesion=10,
            unit_weight=18,
            depth=1.0,
            width=2.0,
            phi_deg=25,
            shape=FoundationShape.RECTANGULAR,
            length=4.0,
        )
        assert result.ultimate_bearing_capacity > 0

    def test_str_representation(self, bc):
        result = bc.terzaghi(
            cohesion=20, unit_weight=18, depth=1.0, width=2.0, phi_deg=25
        )
        s = str(result)
        assert "Terzaghi" in s
        assert "Ultimate" in s
        assert "Allowable" in s


class TestMeyerhof:
    def test_basic_meyerhof(self, bc):
        result = bc.meyerhof(
            cohesion=20,
            unit_weight=18,
            depth=1.5,
            width=2.0,
            phi_deg=30,
        )
        assert result.ultimate_bearing_capacity > 0
        assert result.method == "Meyerhof (1963)"

    def test_meyerhof_square(self, bc):
        result = bc.meyerhof(
            cohesion=10,
            unit_weight=19,
            depth=1.0,
            width=1.5,
            phi_deg=25,
            shape=FoundationShape.SQUARE,
        )
        assert result.ultimate_bearing_capacity > 0

    def test_meyerhof_with_inclination(self, bc):
        result_vertical = bc.meyerhof(
            cohesion=20, unit_weight=18, depth=1.0, width=2.0, phi_deg=30,
            load_inclination_deg=0
        )
        result_inclined = bc.meyerhof(
            cohesion=20, unit_weight=18, depth=1.0, width=2.0, phi_deg=30,
            load_inclination_deg=20
        )
        # Inclined load reduces bearing capacity
        assert result_inclined.ultimate_bearing_capacity < result_vertical.ultimate_bearing_capacity

    def test_meyerhof_invalid_inclination(self, bc):
        with pytest.raises(ValueError, match="inclination"):
            bc.meyerhof(
                cohesion=10,
                unit_weight=18,
                depth=1.0,
                width=2.0,
                phi_deg=25,
                load_inclination_deg=95,
            )

    def test_meyerhof_rectangular_requires_length(self, bc):
        with pytest.raises(ValueError, match="Length must be provided"):
            bc.meyerhof(
                cohesion=10,
                unit_weight=18,
                depth=1.0,
                width=2.0,
                phi_deg=25,
                shape=FoundationShape.RECTANGULAR,
            )


class TestBearingCapacityValidation:
    @pytest.mark.parametrize(
        "kwargs, match",
        [
            ({"cohesion": -1, "unit_weight": 18, "depth": 1, "width": 2, "phi_deg": 25}, "Cohesion"),
            ({"cohesion": 0, "unit_weight": 0, "depth": 1, "width": 2, "phi_deg": 25}, "Unit weight"),
            ({"cohesion": 0, "unit_weight": 18, "depth": -1, "width": 2, "phi_deg": 25}, "depth"),
            ({"cohesion": 0, "unit_weight": 18, "depth": 1, "width": -2, "phi_deg": 25}, "width"),
            ({"cohesion": 0, "unit_weight": 18, "depth": 1, "width": 2, "phi_deg": 95}, "Friction angle"),
            ({"cohesion": 0, "unit_weight": 18, "depth": 1, "width": 2, "phi_deg": 25, "factor_of_safety": 0}, "safety"),
        ],
    )
    def test_terzaghi_validation(self, bc, kwargs, match):
        with pytest.raises(ValueError, match=match):
            bc.terzaghi(**kwargs)
