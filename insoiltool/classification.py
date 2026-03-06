"""
Soil Classification Module

Implements the Unified Soil Classification System (USCS / ASTM D2487)
and AASHTO soil classification.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SoilClassificationResult:
    """Result of soil classification."""

    symbol: str
    description: str
    system: str
    group_index: Optional[float] = None

    def __str__(self) -> str:
        if self.group_index is not None:
            return f"{self.symbol} - {self.description} (GI={self.group_index:.0f})"
        return f"{self.symbol} - {self.description}"


class SoilClassifier:
    """
    Classifies soils using the Unified Soil Classification System (USCS)
    and AASHTO classification method.

    USCS follows ASTM D2487 standard.
    """

    # Gravel-sand boundary
    GRAVEL_SAND_BOUNDARY = 4.75  # mm (No. 4 sieve)
    # Coarse-fine boundary
    COARSE_FINE_BOUNDARY = 0.075  # mm (No. 200 sieve)

    def classify_uscs(
        self,
        percent_gravel: float,
        percent_sand: float,
        percent_fines: float,
        liquid_limit: Optional[float] = None,
        plasticity_index: Optional[float] = None,
        cu: Optional[float] = None,
        cc: Optional[float] = None,
    ) -> SoilClassificationResult:
        """
        Classify soil using USCS (ASTM D2487).

        Args:
            percent_gravel: Percentage of gravel fraction (retained on No. 4 sieve).
            percent_sand: Percentage of sand fraction.
            percent_fines: Percentage passing No. 200 sieve.
            liquid_limit: Liquid limit (%).
            plasticity_index: Plasticity index (%).
            cu: Coefficient of uniformity (D60/D10).
            cc: Coefficient of curvature (D30^2 / (D10 * D60)).

        Returns:
            SoilClassificationResult with USCS symbol and description.

        Raises:
            ValueError: If percentages do not sum to approximately 100 or
                        required parameters are missing.
        """
        total = percent_gravel + percent_sand + percent_fines
        if not (99.0 <= total <= 101.0):
            raise ValueError(
                f"Gravel + Sand + Fines must sum to ~100%, got {total:.1f}%"
            )
        if any(v < 0 or v > 100 for v in [percent_gravel, percent_sand, percent_fines]):
            raise ValueError("All percentages must be between 0 and 100.")

        # --- Coarse-grained soils (< 50% fines) ---
        if percent_fines < 50:
            if percent_gravel > percent_sand:
                return self._classify_gravel(
                    percent_fines, liquid_limit, plasticity_index, cu, cc
                )
            else:
                return self._classify_sand(
                    percent_fines, liquid_limit, plasticity_index, cu, cc
                )
        # --- Fine-grained soils (>= 50% fines) ---
        else:
            return self._classify_fine(liquid_limit, plasticity_index)

    def _classify_gravel(
        self,
        fines: float,
        ll: Optional[float],
        pi: Optional[float],
        cu: Optional[float],
        cc: Optional[float],
    ) -> SoilClassificationResult:
        """Classify gravel soils."""
        if fines < 5:
            # Clean gravels — need Cu and Cc
            if cu is None or cc is None:
                return SoilClassificationResult("GW/GP", "Gravel (well/poorly graded)", "USCS")
            if cu >= 4 and 1 <= cc <= 3:
                return SoilClassificationResult("GW", "Well-graded gravel", "USCS")
            return SoilClassificationResult("GP", "Poorly graded gravel", "USCS")
        elif fines > 12:
            # Gravels with fines — need LL and PI
            if ll is None or pi is None:
                return SoilClassificationResult(
                    "GM/GC", "Silty/clayey gravel (LL/PI needed)", "USCS"
                )
            if pi < 4 or (ll < 25.89 * pi + 4.0 and pi < 7):
                return SoilClassificationResult("GM", "Silty gravel", "USCS")
            return SoilClassificationResult("GC", "Clayey gravel", "USCS")
        else:
            # Borderline (5–12% fines)
            if ll is None or pi is None or cu is None or cc is None:
                return SoilClassificationResult(
                    "GW-GM/GW-GC/GP-GM/GP-GC",
                    "Gravel with fines (dual symbol, LL/PI/Cu/Cc needed)",
                    "USCS",
                )
            well_graded = cu >= 4 and 1 <= cc <= 3
            plastic_fines = pi >= 4
            base = "GW" if well_graded else "GP"
            modifier = "GC" if plastic_fines else "GM"
            symbol = f"{base}-{modifier[-2:]}"
            desc = (
                f"{'Well' if well_graded else 'Poorly'}-graded gravel with "
                f"{'clay' if plastic_fines else 'silt'}"
            )
            return SoilClassificationResult(symbol, desc, "USCS")

    def _classify_sand(
        self,
        fines: float,
        ll: Optional[float],
        pi: Optional[float],
        cu: Optional[float],
        cc: Optional[float],
    ) -> SoilClassificationResult:
        """Classify sand soils."""
        if fines < 5:
            if cu is None or cc is None:
                return SoilClassificationResult("SW/SP", "Sand (well/poorly graded)", "USCS")
            if cu >= 6 and 1 <= cc <= 3:
                return SoilClassificationResult("SW", "Well-graded sand", "USCS")
            return SoilClassificationResult("SP", "Poorly graded sand", "USCS")
        elif fines > 12:
            if ll is None or pi is None:
                return SoilClassificationResult(
                    "SM/SC", "Silty/clayey sand (LL/PI needed)", "USCS"
                )
            if pi < 4 or (ll < 25.89 * pi + 4.0 and pi < 7):
                return SoilClassificationResult("SM", "Silty sand", "USCS")
            return SoilClassificationResult("SC", "Clayey sand", "USCS")
        else:
            if ll is None or pi is None or cu is None or cc is None:
                return SoilClassificationResult(
                    "SW-SM/SW-SC/SP-SM/SP-SC",
                    "Sand with fines (dual symbol, LL/PI/Cu/Cc needed)",
                    "USCS",
                )
            well_graded = cu >= 6 and 1 <= cc <= 3
            plastic_fines = pi >= 4
            base = "SW" if well_graded else "SP"
            modifier = "SC" if plastic_fines else "SM"
            symbol = f"{base}-{modifier[-2:]}"
            desc = (
                f"{'Well' if well_graded else 'Poorly'}-graded sand with "
                f"{'clay' if plastic_fines else 'silt'}"
            )
            return SoilClassificationResult(symbol, desc, "USCS")

    def _classify_fine(
        self, ll: Optional[float], pi: Optional[float]
    ) -> SoilClassificationResult:
        """Classify fine-grained soils using Casagrande plasticity chart."""
        if ll is None or pi is None:
            raise ValueError(
                "Liquid limit and plasticity index are required for fine-grained soils."
            )
        a_line_pi = 0.73 * (ll - 20)
        if ll < 50:
            # Low plasticity
            if pi > a_line_pi and pi >= 7:
                return SoilClassificationResult("CL", "Lean clay (low plasticity)", "USCS")
            elif pi < 4 or pi < a_line_pi:
                return SoilClassificationResult("ML", "Silt (low plasticity)", "USCS")
            else:
                return SoilClassificationResult("CL-ML", "Silty clay (low plasticity)", "USCS")
        else:
            # High plasticity
            if pi > a_line_pi:
                return SoilClassificationResult("CH", "Fat clay (high plasticity)", "USCS")
            elif ll >= 50 and pi < a_line_pi:
                return SoilClassificationResult("MH", "Elastic silt (high plasticity)", "USCS")
            else:
                return SoilClassificationResult("MH/CH", "Silt or clay (high plasticity)", "USCS")

    def classify_aashto(
        self,
        percent_passing_no10: float,
        percent_passing_no40: float,
        percent_passing_no200: float,
        liquid_limit: Optional[float] = None,
        plasticity_index: Optional[float] = None,
    ) -> SoilClassificationResult:
        """
        Classify soil using AASHTO classification (AASHTO M 145).

        Args:
            percent_passing_no10: % passing No. 10 sieve (2.0 mm).
            percent_passing_no40: % passing No. 40 sieve (0.425 mm).
            percent_passing_no200: % passing No. 200 sieve (0.075 mm).
            liquid_limit: Liquid limit (%).
            plasticity_index: Plasticity index (%).

        Returns:
            SoilClassificationResult with AASHTO group symbol.

        Raises:
            ValueError: If input parameters are out of valid range.
        """
        for name, val in [
            ("No. 10", percent_passing_no10),
            ("No. 40", percent_passing_no40),
            ("No. 200", percent_passing_no200),
        ]:
            if not (0 <= val <= 100):
                raise ValueError(f"{name} sieve % must be between 0 and 100, got {val}.")

        p200 = percent_passing_no200
        p40 = percent_passing_no40
        p10 = percent_passing_no10
        ll = liquid_limit if liquid_limit is not None else 0
        pi = plasticity_index if plasticity_index is not None else 0

        gi = self._group_index(p200, ll, pi)

        # A-1 granular
        if p200 <= 25 and p40 <= 50:
            if pi <= 6:
                return SoilClassificationResult(
                    "A-1-a", "Stone fragments, gravel and sand", "AASHTO", gi
                )
        if p200 <= 35 and p40 <= 50 and pi <= 6:
            return SoilClassificationResult("A-1-b", "Stone fragments, gravel and sand", "AASHTO", gi)

        # A-3 fine sand
        if p200 <= 10 and (liquid_limit is None or ll == 0) and (plasticity_index is None or pi == 0):
            return SoilClassificationResult("A-3", "Fine sand", "AASHTO", gi)

        # A-2 granular with fines
        if p200 <= 35:
            if ll <= 40 and pi <= 10:
                return SoilClassificationResult("A-2-4", "Silty or clayey gravel and sand", "AASHTO", gi)
            if ll <= 40 and pi > 10:
                return SoilClassificationResult("A-2-5", "Silty or clayey gravel and sand", "AASHTO", gi)
            if ll > 40 and pi <= 10:
                return SoilClassificationResult("A-2-6", "Silty or clayey gravel and sand", "AASHTO", gi)
            return SoilClassificationResult("A-2-7", "Silty or clayey gravel and sand", "AASHTO", gi)

        # Silt-clay (> 35% passing No. 200)
        if ll <= 40 and pi <= 10:
            return SoilClassificationResult("A-4", "Silty soils", "AASHTO", gi)
        if ll <= 40 and pi > 10:
            return SoilClassificationResult("A-5", "Silty soils", "AASHTO", gi)
        if ll > 40 and pi <= 10 and pi >= (ll - 30):
            return SoilClassificationResult("A-6", "Clayey soils", "AASHTO", gi)
        return SoilClassificationResult("A-7", "Clayey soils", "AASHTO", gi)

    @staticmethod
    def _group_index(p200: float, ll: float, pi: float) -> float:
        """Calculate AASHTO group index (GI)."""
        f = p200 - 35
        gi = (f * (0.2 + 0.005 * (ll - 40))) + (0.01 * (p200 - 15) * (pi - 10))
        return max(0.0, round(gi, 1))
