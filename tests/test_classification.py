"""Tests for soil classification module."""

import pytest

from insoiltool.classification import SoilClassifier, SoilClassificationResult


@pytest.fixture
def classifier():
    return SoilClassifier()


class TestUSCSClassification:
    """Tests for USCS classification."""

    def test_well_graded_gravel(self, classifier):
        """GW: gravel dominant, clean, Cu>=4, 1<=Cc<=3."""
        result = classifier.classify_uscs(
            percent_gravel=65, percent_sand=31, percent_fines=4, cu=8.0, cc=2.1
        )
        assert result.symbol == "GW"
        assert "gravel" in result.description.lower()
        assert result.system == "USCS"

    def test_poorly_graded_gravel(self, classifier):
        """GP: gravel dominant, clean, fails Cu or Cc criteria."""
        result = classifier.classify_uscs(
            percent_gravel=70, percent_sand=28, percent_fines=2, cu=1.5, cc=0.8
        )
        assert result.symbol == "GP"

    def test_well_graded_sand(self, classifier):
        """SW: sand dominant, clean, Cu>=6, 1<=Cc<=3."""
        result = classifier.classify_uscs(
            percent_gravel=10, percent_sand=86, percent_fines=4, cu=9.0, cc=1.5
        )
        assert result.symbol == "SW"

    def test_poorly_graded_sand(self, classifier):
        """SP: sand dominant, clean, fails Cu or Cc criteria."""
        result = classifier.classify_uscs(
            percent_gravel=5, percent_sand=91, percent_fines=4, cu=2.0, cc=1.0
        )
        assert result.symbol == "SP"

    def test_silty_gravel(self, classifier):
        """GM: gravel with non-plastic fines (PI < 4)."""
        result = classifier.classify_uscs(
            percent_gravel=55, percent_sand=25, percent_fines=20, liquid_limit=20, plasticity_index=3
        )
        assert result.symbol == "GM"

    def test_clayey_gravel(self, classifier):
        """GC: gravel with plastic fines (PI >= 7)."""
        result = classifier.classify_uscs(
            percent_gravel=55, percent_sand=20, percent_fines=25, liquid_limit=35, plasticity_index=15
        )
        assert result.symbol == "GC"

    def test_silty_sand(self, classifier):
        """SM: sand with non-plastic fines."""
        result = classifier.classify_uscs(
            percent_gravel=5, percent_sand=75, percent_fines=20, liquid_limit=18, plasticity_index=3
        )
        assert result.symbol == "SM"

    def test_clayey_sand(self, classifier):
        """SC: sand with plastic fines."""
        result = classifier.classify_uscs(
            percent_gravel=5, percent_sand=75, percent_fines=20, liquid_limit=38, plasticity_index=18
        )
        assert result.symbol == "SC"

    def test_lean_clay(self, classifier):
        """CL: fine-grained soil, LL < 50, PI above A-line, PI >= 7."""
        result = classifier.classify_uscs(
            percent_gravel=2, percent_sand=15, percent_fines=83, liquid_limit=40, plasticity_index=20
        )
        assert result.symbol == "CL"

    def test_fat_clay(self, classifier):
        """CH: fine-grained, LL >= 50, PI above A-line."""
        result = classifier.classify_uscs(
            percent_gravel=0, percent_sand=10, percent_fines=90, liquid_limit=65, plasticity_index=40
        )
        assert result.symbol == "CH"

    def test_low_plasticity_silt(self, classifier):
        """ML: fine-grained, LL < 50, PI below A-line."""
        result = classifier.classify_uscs(
            percent_gravel=2, percent_sand=15, percent_fines=83, liquid_limit=30, plasticity_index=3
        )
        assert result.symbol == "ML"

    def test_high_plasticity_silt(self, classifier):
        """MH: fine-grained, LL >= 50, PI below A-line."""
        result = classifier.classify_uscs(
            percent_gravel=0, percent_sand=10, percent_fines=90, liquid_limit=60, plasticity_index=10
        )
        assert result.symbol == "MH"

    def test_percentages_not_sum_to_100_raises(self, classifier):
        with pytest.raises(ValueError, match="sum to ~100%"):
            classifier.classify_uscs(
                percent_gravel=30, percent_sand=30, percent_fines=30
            )

    def test_negative_percentage_raises(self, classifier):
        with pytest.raises(ValueError, match="between 0 and 100"):
            classifier.classify_uscs(
                percent_gravel=-5, percent_sand=65, percent_fines=40
            )

    def test_fine_grained_missing_ll_pi_raises(self, classifier):
        with pytest.raises(ValueError, match="Liquid limit and plasticity index"):
            classifier.classify_uscs(
                percent_gravel=2, percent_sand=8, percent_fines=90
            )

    def test_str_representation(self, classifier):
        result = classifier.classify_uscs(
            percent_gravel=65, percent_sand=30, percent_fines=5, cu=8.0, cc=2.1
        )
        s = str(result)
        assert "GW" in s
        assert "-" in s


class TestAASHTOClassification:
    """Tests for AASHTO classification."""

    def test_a1a_granular(self, classifier):
        """A-1-a: coarse granular, low fines, non-plastic."""
        result = classifier.classify_aashto(
            percent_passing_no10=40,
            percent_passing_no40=30,
            percent_passing_no200=10,
        )
        assert result.symbol == "A-1-a"
        assert result.system == "AASHTO"

    def test_a4_silty(self, classifier):
        """A-4: silt with LL<=40, PI<=10, p200>35."""
        result = classifier.classify_aashto(
            percent_passing_no10=90,
            percent_passing_no40=75,
            percent_passing_no200=50,
            liquid_limit=35,
            plasticity_index=8,
        )
        assert result.symbol == "A-4"

    def test_a7_clayey(self, classifier):
        """A-7: clay with LL>40, PI beyond threshold."""
        result = classifier.classify_aashto(
            percent_passing_no10=95,
            percent_passing_no40=85,
            percent_passing_no200=60,
            liquid_limit=55,
            plasticity_index=30,
        )
        assert result.symbol == "A-7"

    def test_invalid_sieve_percent_raises(self, classifier):
        with pytest.raises(ValueError, match="No. 10"):
            classifier.classify_aashto(
                percent_passing_no10=110,
                percent_passing_no40=75,
                percent_passing_no200=50,
            )

    def test_group_index_non_negative(self, classifier):
        result = classifier.classify_aashto(
            percent_passing_no10=30,
            percent_passing_no40=20,
            percent_passing_no200=10,
        )
        assert result.group_index >= 0
