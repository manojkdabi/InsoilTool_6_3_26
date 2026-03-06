"""
Atterberg Limits Module

Calculates consistency indices and related soil properties from
Atterberg limit tests (ASTM D4318).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AtterbergResult:
    """Result of Atterberg limits analysis."""

    liquid_limit: float
    plastic_limit: float
    plasticity_index: float
    shrinkage_limit: Optional[float]
    liquidity_index: Optional[float]
    consistency_index: Optional[float]

    def __str__(self) -> str:
        lines = [
            f"Liquid Limit (LL):       {self.liquid_limit:.1f}%",
            f"Plastic Limit (PL):      {self.plastic_limit:.1f}%",
            f"Plasticity Index (PI):   {self.plasticity_index:.1f}%",
        ]
        if self.shrinkage_limit is not None:
            lines.append(f"Shrinkage Limit (SL):    {self.shrinkage_limit:.1f}%")
        if self.liquidity_index is not None:
            lines.append(f"Liquidity Index (LI):    {self.liquidity_index:.3f}")
        if self.consistency_index is not None:
            lines.append(f"Consistency Index (CI):  {self.consistency_index:.3f}")
        return "\n".join(lines)


class AtterbergLimits:
    """
    Computes Atterberg limits and derived consistency parameters.

    Liquid Limit (LL): moisture content at which soil transitions from
        plastic to liquid state (Casagrande cup or fall cone, ASTM D4318).
    Plastic Limit (PL): moisture content below which the soil is not plastic.
    Plasticity Index (PI): LL - PL.
    Shrinkage Limit (SL): moisture content below which further drying
        causes no volume reduction.
    Liquidity Index (LI): (w - PL) / PI.
    Consistency Index (CI): (LL - w) / PI.
    """

    def compute(
        self,
        liquid_limit: float,
        plastic_limit: float,
        natural_water_content: Optional[float] = None,
        shrinkage_limit: Optional[float] = None,
    ) -> AtterbergResult:
        """
        Compute Atterberg limits and consistency indices.

        Args:
            liquid_limit: Liquid limit (%).
            plastic_limit: Plastic limit (%).
            natural_water_content: In-situ water content (%). Required for
                liquidity and consistency indices.
            shrinkage_limit: Shrinkage limit (%) if available.

        Returns:
            AtterbergResult with all computed values.

        Raises:
            ValueError: If input values are physically inconsistent.
        """
        self._validate(liquid_limit, plastic_limit, shrinkage_limit)

        pi = liquid_limit - plastic_limit

        li: Optional[float] = None
        ci: Optional[float] = None
        if natural_water_content is not None:
            if natural_water_content < 0:
                raise ValueError(
                    f"Natural water content must be >= 0, got {natural_water_content}."
                )
            if pi > 0:
                li = (natural_water_content - plastic_limit) / pi
                ci = (liquid_limit - natural_water_content) / pi
            else:
                li = None
                ci = None

        return AtterbergResult(
            liquid_limit=liquid_limit,
            plastic_limit=plastic_limit,
            plasticity_index=pi,
            shrinkage_limit=shrinkage_limit,
            liquidity_index=li,
            consistency_index=ci,
        )

    @staticmethod
    def _validate(
        ll: float, pl: float, sl: Optional[float]
    ) -> None:
        """Validate Atterberg limit values."""
        if ll < 0 or pl < 0:
            raise ValueError("Liquid limit and plastic limit must be >= 0.")
        if ll > 100 or pl > 100:
            raise ValueError("Liquid limit and plastic limit must be <= 100%.")
        if pl > ll:
            raise ValueError(
                f"Plastic limit ({pl}%) cannot exceed liquid limit ({ll}%)."
            )
        if sl is not None:
            if sl < 0:
                raise ValueError(f"Shrinkage limit must be >= 0, got {sl}.")
            if sl > pl:
                raise ValueError(
                    f"Shrinkage limit ({sl}%) cannot exceed plastic limit ({pl}%)."
                )

    @staticmethod
    def activity(plasticity_index: float, percent_clay: float) -> float:
        """
        Compute Skempton's activity (A = PI / % clay).

        Args:
            plasticity_index: Plasticity index (%).
            percent_clay: Percentage of clay-sized particles (< 0.002 mm).

        Returns:
            Activity value (dimensionless).

        Raises:
            ValueError: If percent_clay is zero or negative.
        """
        if percent_clay <= 0:
            raise ValueError(
                f"Percent clay must be > 0 to compute activity, got {percent_clay}."
            )
        return plasticity_index / percent_clay

    @staticmethod
    def describe_plasticity(plasticity_index: float) -> str:
        """
        Describe plasticity based on plasticity index value.

        Args:
            plasticity_index: Plasticity index (%).

        Returns:
            Human-readable plasticity description.
        """
        if plasticity_index < 0:
            raise ValueError(f"Plasticity index must be >= 0, got {plasticity_index}.")
        if plasticity_index == 0:
            return "Non-plastic"
        if plasticity_index < 7:
            return "Slightly plastic"
        if plasticity_index < 17:
            return "Medium plastic"
        if plasticity_index < 35:
            return "Highly plastic"
        return "Very highly plastic"

    @staticmethod
    def describe_consistency(liquidity_index: float) -> str:
        """
        Describe soil consistency based on liquidity index.

        Args:
            liquidity_index: Liquidity index (LI).

        Returns:
            Human-readable consistency description.
        """
        if liquidity_index < 0:
            return "Very stiff / hard"
        if liquidity_index < 0.25:
            return "Stiff"
        if liquidity_index < 0.50:
            return "Medium stiff"
        if liquidity_index < 0.75:
            return "Soft"
        if liquidity_index < 1.0:
            return "Very soft"
        return "Liquid"
