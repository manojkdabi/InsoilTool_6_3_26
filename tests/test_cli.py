"""Tests for CLI interface."""

import pytest

from insoiltool.cli import build_parser, main, _parse_grainsize_data


class TestCLIVersion:
    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "6.3.26" in out


class TestCLIClassifyUSCS:
    def test_clean_gravel(self, capsys):
        rc = main(["classify-uscs", "--gravel", "65", "--sand", "30", "--fines", "5",
                   "--cu", "8.0", "--cc", "2.1"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "GW" in out

    def test_fine_grained_clay(self, capsys):
        rc = main(["classify-uscs", "--gravel", "2", "--sand", "15", "--fines", "83",
                   "--ll", "40", "--pi", "20"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "CL" in out

    def test_invalid_percentages(self, capsys):
        rc = main(["classify-uscs", "--gravel", "50", "--sand", "50", "--fines", "50"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Error" in err


class TestCLIClassifyAASHTO:
    def test_aashto_a4(self, capsys):
        rc = main(["classify-aashto", "--p10", "90", "--p40", "75", "--p200", "50",
                   "--ll", "35", "--pi", "8"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "A-4" in out

    def test_invalid_sieve_percent(self, capsys):
        rc = main(["classify-aashto", "--p10", "110", "--p40", "75", "--p200", "50"])
        assert rc == 1


class TestCLIAtterberg:
    def test_basic_atterberg(self, capsys):
        rc = main(["atterberg", "--ll", "45", "--pl", "22"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Plasticity Index" in out
        assert "23" in out  # PI = 45 - 22

    def test_with_natural_water_content(self, capsys):
        rc = main(["atterberg", "--ll", "45", "--pl", "22", "--wn", "35"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Liquidity Index" in out

    def test_with_clay_pct(self, capsys):
        rc = main(["atterberg", "--ll", "45", "--pl", "22", "--clay-pct", "30"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Activity" in out

    def test_invalid_pl_gt_ll(self, capsys):
        rc = main(["atterberg", "--ll", "20", "--pl", "30"])
        assert rc == 1


class TestCLIGrainSize:
    def test_basic_grainsize(self, capsys):
        rc = main(["grainsize", "--data", "75,100 19,85 4.75,60 2,45 0.425,28 0.075,10"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Gravel" in out
        assert "Sand" in out

    def test_invalid_data_format(self, capsys):
        rc = main(["grainsize", "--data", "75-100 19-85"])
        assert rc == 1


class TestCLIBearing:
    def test_terzaghi_strip(self, capsys):
        rc = main(["bearing", "--method", "terzaghi",
                   "--c", "20", "--gamma", "18", "--df", "1.5", "--b", "2.0", "--phi", "30"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Terzaghi" in out
        assert "Ultimate" in out

    def test_meyerhof_square(self, capsys):
        rc = main(["bearing", "--method", "meyerhof",
                   "--c", "10", "--gamma", "19", "--df", "1.0", "--b", "1.5",
                   "--phi", "25", "--shape", "square"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Meyerhof" in out

    def test_invalid_cohesion(self, capsys):
        rc = main(["bearing", "--c", "-5", "--gamma", "18",
                   "--df", "1.0", "--b", "2.0", "--phi", "25"])
        assert rc == 1


class TestParseGrainsizeData:
    def test_valid_parse(self):
        data = _parse_grainsize_data("4.75,60 0.075,10")
        assert len(data) == 2
        assert data[0] == (4.75, 60.0)
        assert data[1] == (0.075, 10.0)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="expected 'size,percent'"):
            _parse_grainsize_data("4.75-60 0.075-10")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="No grain size"):
            _parse_grainsize_data("   ")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="Invalid numeric"):
            _parse_grainsize_data("abc,60")
