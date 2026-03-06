"""Tests for grain size distribution module."""

import pytest

from insoiltool.grain_size import GrainSizeDistribution


# Typical graded gravel/sand data (size_mm, percent_passing)
SAMPLE_DATA = [
    (75.0, 100.0),
    (19.0, 85.0),
    (9.5, 72.0),
    (4.75, 58.0),
    (2.0, 45.0),
    (0.425, 28.0),
    (0.075, 10.0),
]


@pytest.fixture
def gs():
    return GrainSizeDistribution()


class TestGrainSizeAnalyze:
    def test_fractions_sum_to_100(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        total = result.percent_gravel + result.percent_sand + result.percent_fines
        assert total == pytest.approx(100.0, abs=0.5)

    def test_fines_match_boundary(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        # Data at 0.075 mm is 10%, so fines ~ 10%
        assert result.percent_fines == pytest.approx(10.0, abs=1.0)

    def test_d10_interpolation(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        # D10 is at 10% passing; from data that's right at 0.075 mm
        assert result.d10 is not None
        assert 0.05 <= result.d10 <= 0.15

    def test_d50_interpolation(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        assert result.d50 is not None
        # D50 at 50% passing; from data between 2.0 mm (45%) and 4.75 mm (58%)
        assert 2.0 <= result.d50 <= 4.75

    def test_d60_greater_than_d30_greater_than_d10(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        if result.d10 and result.d30 and result.d60:
            assert result.d10 <= result.d30 <= result.d60

    def test_cu_and_cc_computed(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        assert result.cu is not None
        assert result.cc is not None
        assert result.cu > 0
        assert result.cc > 0

    def test_effective_size_equals_d10(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        assert result.effective_size == result.d10

    def test_gradation_description(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        assert isinstance(result.gradation, str)
        assert len(result.gradation) > 0

    def test_str_representation(self, gs):
        result = gs.analyze(SAMPLE_DATA)
        s = str(result)
        assert "Gravel" in s
        assert "Sand" in s
        assert "Fines" in s

    def test_sorted_order_independent(self, gs):
        """Results should be the same regardless of input order."""
        reversed_data = list(reversed(SAMPLE_DATA))
        result1 = gs.analyze(SAMPLE_DATA)
        result2 = gs.analyze(reversed_data)
        assert result1.d50 == pytest.approx(result2.d50, rel=1e-6)


class TestGrainSizeValidation:
    def test_less_than_2_points_raises(self, gs):
        with pytest.raises(ValueError, match="2 data points"):
            gs.analyze([(4.75, 60.0)])

    def test_non_monotonic_passing_raises(self, gs):
        bad_data = [(4.75, 60.0), (0.425, 70.0), (0.075, 10.0)]
        with pytest.raises(ValueError, match="must decrease"):
            gs.analyze(bad_data)

    def test_negative_size_raises(self, gs):
        with pytest.raises(ValueError, match="Particle sizes"):
            gs.analyze([(-1.0, 80.0), (0.075, 10.0)])

    def test_percent_over_100_raises(self, gs):
        with pytest.raises(ValueError, match="between 0 and 100"):
            gs.analyze([(4.75, 110.0), (0.075, 10.0)])

    def test_percent_below_0_raises(self, gs):
        with pytest.raises(ValueError, match="between 0 and 100"):
            gs.analyze([(4.75, 60.0), (0.075, -5.0)])
