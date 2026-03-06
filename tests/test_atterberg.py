"""Tests for Atterberg limits module."""

import pytest

from insoiltool.atterberg import AtterbergLimits


@pytest.fixture
def al():
    return AtterbergLimits()


class TestAtterbergCompute:
    def test_basic_result(self, al):
        result = al.compute(liquid_limit=45, plastic_limit=20)
        assert result.liquid_limit == 45
        assert result.plastic_limit == 20
        assert result.plasticity_index == 25
        assert result.shrinkage_limit is None
        assert result.liquidity_index is None
        assert result.consistency_index is None

    def test_with_natural_water_content(self, al):
        result = al.compute(liquid_limit=45, plastic_limit=20, natural_water_content=35)
        assert result.liquidity_index == pytest.approx((35 - 20) / 25)
        assert result.consistency_index == pytest.approx((45 - 35) / 25)

    def test_with_shrinkage_limit(self, al):
        result = al.compute(liquid_limit=45, plastic_limit=20, shrinkage_limit=14)
        assert result.shrinkage_limit == 14

    def test_pl_equals_ll_gives_zero_pi(self, al):
        result = al.compute(liquid_limit=30, plastic_limit=30)
        assert result.plasticity_index == 0

    def test_pl_greater_than_ll_raises(self, al):
        with pytest.raises(ValueError, match="cannot exceed"):
            al.compute(liquid_limit=20, plastic_limit=25)

    def test_negative_ll_raises(self, al):
        with pytest.raises(ValueError, match=">= 0"):
            al.compute(liquid_limit=-5, plastic_limit=10)

    def test_sl_greater_than_pl_raises(self, al):
        with pytest.raises(ValueError, match="cannot exceed"):
            al.compute(liquid_limit=45, plastic_limit=20, shrinkage_limit=25)

    def test_negative_water_content_raises(self, al):
        with pytest.raises(ValueError, match=">= 0"):
            al.compute(liquid_limit=45, plastic_limit=20, natural_water_content=-1)

    def test_str_representation(self, al):
        result = al.compute(liquid_limit=45, plastic_limit=20, natural_water_content=35)
        s = str(result)
        assert "Liquid Limit" in s
        assert "Plasticity Index" in s
        assert "Liquidity Index" in s


class TestAtterbergActivity:
    def test_activity_calculation(self):
        assert AtterbergLimits.activity(30, 40) == pytest.approx(0.75)

    def test_zero_clay_raises(self):
        with pytest.raises(ValueError, match="> 0"):
            AtterbergLimits.activity(30, 0)

    def test_negative_clay_raises(self):
        with pytest.raises(ValueError, match="> 0"):
            AtterbergLimits.activity(30, -5)


class TestDescribePlasticity:
    @pytest.mark.parametrize(
        "pi, expected",
        [
            (0, "Non-plastic"),
            (3, "Slightly plastic"),
            (12, "Medium plastic"),
            (25, "Highly plastic"),
            (40, "Very highly plastic"),
        ],
    )
    def test_plasticity_descriptions(self, pi, expected):
        assert AtterbergLimits.describe_plasticity(pi) == expected

    def test_negative_pi_raises(self):
        with pytest.raises(ValueError, match=">= 0"):
            AtterbergLimits.describe_plasticity(-1)


class TestDescribeConsistency:
    @pytest.mark.parametrize(
        "li, expected",
        [
            (-0.5, "Very stiff / hard"),
            (0.1, "Stiff"),
            (0.35, "Medium stiff"),
            (0.6, "Soft"),
            (0.8, "Very soft"),
            (1.2, "Liquid"),
        ],
    )
    def test_consistency_descriptions(self, li, expected):
        assert AtterbergLimits.describe_consistency(li) == expected
