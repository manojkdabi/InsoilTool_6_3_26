"""
Grain Size Distribution Module

Processes grain size analysis data and computes standard descriptors
(ASTM D422 / D6913).
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class GrainSizeResult:
    """Results of grain size distribution analysis."""

    d10: Optional[float]
    d30: Optional[float]
    d50: Optional[float]
    d60: Optional[float]
    cu: Optional[float]
    cc: Optional[float]
    percent_gravel: float
    percent_sand: float
    percent_fines: float
    effective_size: Optional[float]
    gradation: str
    data_points: List[Tuple[float, float]] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"Gradation:       {self.gradation}",
            f"% Gravel (> 4.75 mm):  {self.percent_gravel:.1f}%",
            f"% Sand (0.075–4.75 mm): {self.percent_sand:.1f}%",
            f"% Fines (< 0.075 mm):  {self.percent_fines:.1f}%",
        ]
        for label, val in [
            ("D10 (mm)", self.d10),
            ("D30 (mm)", self.d30),
            ("D50 (mm)", self.d50),
            ("D60 (mm)", self.d60),
            ("Cu (D60/D10)", self.cu),
            ("Cc (D30²/(D10·D60))", self.cc),
        ]:
            if val is not None:
                lines.append(f"{label:25s}: {val:.4f}")
            else:
                lines.append(f"{label:25s}: N/A")
        return "\n".join(lines)


class GrainSizeDistribution:
    """
    Analyzes grain size distribution data from sieve and hydrometer tests.

    Grain size data is supplied as a list of (particle_size_mm, percent_passing)
    tuples, ordered from largest to smallest particle size.
    """

    # Boundary sizes in mm
    GRAVEL_BOUNDARY = 4.75
    FINES_BOUNDARY = 0.075

    def analyze(
        self, data: List[Tuple[float, float]]
    ) -> GrainSizeResult:
        """
        Analyze grain size distribution data.

        Args:
            data: List of (particle_size_mm, percent_passing) tuples.
                  Percent passing must decrease with decreasing particle size.

        Returns:
            GrainSizeResult with computed distribution parameters.

        Raises:
            ValueError: If data is invalid (< 2 points, invalid percentages,
                        non-monotonic sizes, etc.).
        """
        self._validate(data)
        sorted_data = sorted(data, key=lambda x: x[0], reverse=True)

        d10 = self._interpolate_dx(sorted_data, 10.0)
        d30 = self._interpolate_dx(sorted_data, 30.0)
        d50 = self._interpolate_dx(sorted_data, 50.0)
        d60 = self._interpolate_dx(sorted_data, 60.0)

        cu: Optional[float] = None
        cc: Optional[float] = None
        if d10 is not None and d60 is not None and d10 > 0:
            cu = d60 / d10
        if d10 is not None and d30 is not None and d60 is not None and d10 > 0 and d60 > 0:
            cc = (d30 ** 2) / (d10 * d60)

        percent_gravel, percent_sand, percent_fines = self._fractions(sorted_data)
        gradation = self._describe_gradation(cu, cc, percent_fines)

        return GrainSizeResult(
            d10=d10,
            d30=d30,
            d50=d50,
            d60=d60,
            cu=cu,
            cc=cc,
            percent_gravel=percent_gravel,
            percent_sand=percent_sand,
            percent_fines=percent_fines,
            effective_size=d10,
            gradation=gradation,
            data_points=sorted_data,
        )

    @staticmethod
    def _validate(data: List[Tuple[float, float]]) -> None:
        """Validate grain size data."""
        if len(data) < 2:
            raise ValueError("At least 2 data points are required.")
        sizes = [d[0] for d in data]
        percents = [d[1] for d in data]
        if any(s <= 0 for s in sizes):
            raise ValueError("Particle sizes must be > 0.")
        if any(p < 0 or p > 100 for p in percents):
            raise ValueError("Percent passing values must be between 0 and 100.")
        sorted_by_size = sorted(data, key=lambda x: x[0], reverse=True)
        passing = [d[1] for d in sorted_by_size]
        for i in range(1, len(passing)):
            if passing[i] > passing[i - 1]:
                raise ValueError(
                    "Percent passing must decrease (or stay equal) as particle size decreases."
                )

    @staticmethod
    def _interpolate_dx(
        sorted_data: List[Tuple[float, float]], target_percent: float
    ) -> Optional[float]:
        """
        Interpolate particle size at a given percent passing using log-linear
        interpolation (log of particle size is linear with percent passing).
        """
        for i in range(len(sorted_data) - 1):
            size_upper, pct_upper = sorted_data[i]
            size_lower, pct_lower = sorted_data[i + 1]
            if pct_lower <= target_percent <= pct_upper:
                if pct_upper == pct_lower:
                    return size_upper
                log_size = math.log(size_lower) + (
                    (target_percent - pct_lower)
                    / (pct_upper - pct_lower)
                    * (math.log(size_upper) - math.log(size_lower))
                )
                return math.exp(log_size)
        return None

    def _fractions(
        self, sorted_data: List[Tuple[float, float]]
    ) -> Tuple[float, float, float]:
        """Compute percent gravel, sand, and fines."""
        pct_at_gravel = self._interpolate_percent(sorted_data, self.GRAVEL_BOUNDARY)
        pct_at_fines = self._interpolate_percent(sorted_data, self.FINES_BOUNDARY)

        # Percent retained at gravel boundary = 100 - percent passing gravel size
        pct_coarser_than_gravel = 100.0 - pct_at_gravel
        pct_finer_than_fines = pct_at_fines

        percent_gravel = pct_coarser_than_gravel
        percent_fines = pct_finer_than_fines
        percent_sand = 100.0 - percent_gravel - percent_fines

        return (
            max(0.0, percent_gravel),
            max(0.0, percent_sand),
            max(0.0, percent_fines),
        )

    @staticmethod
    def _interpolate_percent(
        sorted_data: List[Tuple[float, float]], target_size: float
    ) -> float:
        """Interpolate percent passing at a given particle size."""
        # Check bounds
        if target_size >= sorted_data[0][0]:
            return sorted_data[0][1]
        if target_size <= sorted_data[-1][0]:
            return sorted_data[-1][1]
        for i in range(len(sorted_data) - 1):
            size_upper, pct_upper = sorted_data[i]
            size_lower, pct_lower = sorted_data[i + 1]
            if size_lower <= target_size <= size_upper:
                if size_upper == size_lower:
                    return pct_upper
                log_pct = pct_lower + (
                    (math.log(target_size) - math.log(size_lower))
                    / (math.log(size_upper) - math.log(size_lower))
                    * (pct_upper - pct_lower)
                )
                return log_pct
        return 0.0

    @staticmethod
    def _describe_gradation(
        cu: Optional[float], cc: Optional[float], percent_fines: float
    ) -> str:
        """Describe gradation quality."""
        if percent_fines > 50:
            return "Fine-grained (sieve analysis alone insufficient)"
        if cu is None or cc is None:
            return "Indeterminate"
        if cu >= 4 and 1.0 <= cc <= 3.0:
            return "Well-graded"
        if cu < 2:
            return "Uniform (gap or single size)"
        return "Poorly graded"
