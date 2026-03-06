"""
Bearing Capacity Module

Computes ultimate and allowable bearing capacity of shallow foundations
using Terzaghi's (1943) and Meyerhof's (1963) equations.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FoundationShape(str, Enum):
    """Foundation shape options."""

    STRIP = "strip"
    SQUARE = "square"
    CIRCULAR = "circular"
    RECTANGULAR = "rectangular"


@dataclass
class BearingCapacityResult:
    """Result of bearing capacity calculation."""

    method: str
    ultimate_bearing_capacity: float
    allowable_bearing_capacity: float
    factor_of_safety: float
    shape: FoundationShape
    phi_deg: float
    cohesion: float
    unit_weight: float
    depth: float
    width: float

    def __str__(self) -> str:
        return (
            f"Method:                    {self.method}\n"
            f"Foundation shape:          {self.shape.value}\n"
            f"Friction angle (φ):        {self.phi_deg:.1f}°\n"
            f"Cohesion (c):              {self.cohesion:.2f} kPa\n"
            f"Unit weight (γ):           {self.unit_weight:.2f} kN/m³\n"
            f"Foundation depth (Df):     {self.depth:.2f} m\n"
            f"Foundation width (B):      {self.width:.2f} m\n"
            f"Ultimate capacity (qu):    {self.ultimate_bearing_capacity:.2f} kPa\n"
            f"Factor of safety (FS):     {self.factor_of_safety:.1f}\n"
            f"Allowable capacity (qa):   {self.allowable_bearing_capacity:.2f} kPa"
        )


class BearingCapacity:
    """
    Calculates ultimate and allowable bearing capacity of shallow foundations.

    Two classical methods are implemented:
    - Terzaghi (1943): original bearing capacity equation with shape factors.
    - Meyerhof (1963): general bearing capacity equation with shape, depth,
      and inclination factors.
    """

    def terzaghi(
        self,
        cohesion: float,
        unit_weight: float,
        depth: float,
        width: float,
        phi_deg: float,
        shape: FoundationShape = FoundationShape.STRIP,
        factor_of_safety: float = 3.0,
        length: Optional[float] = None,
    ) -> BearingCapacityResult:
        """
        Compute bearing capacity using Terzaghi's (1943) equation.

        qu = c·Nc·sc + q·Nq + 0.5·γ·B·Nγ·sγ

        Args:
            cohesion: Soil cohesion c (kPa).
            unit_weight: Soil unit weight γ (kN/m³).
            depth: Foundation depth Df (m).
            width: Foundation width B (m).
            phi_deg: Soil internal friction angle φ (degrees).
            shape: Foundation shape (strip, square, circular, rectangular).
            factor_of_safety: Desired factor of safety (default 3.0).
            length: Foundation length L (m); required for rectangular shape.

        Returns:
            BearingCapacityResult with ultimate and allowable capacities.

        Raises:
            ValueError: If input values are invalid or length is missing for
                        rectangular shape.
        """
        self._validate_inputs(cohesion, unit_weight, depth, width, phi_deg, factor_of_safety)
        if shape == FoundationShape.RECTANGULAR and length is None:
            raise ValueError("Length must be provided for rectangular foundations.")

        phi = math.radians(phi_deg)
        nc, nq, ng = self._terzaghi_factors(phi)
        sc, sq, sg = self._terzaghi_shape(shape, width, length)

        q = unit_weight * depth  # surcharge at foundation level
        qu = cohesion * nc * sc + q * nq + 0.5 * unit_weight * width * ng * sg
        qa = qu / factor_of_safety

        return BearingCapacityResult(
            method="Terzaghi (1943)",
            ultimate_bearing_capacity=qu,
            allowable_bearing_capacity=qa,
            factor_of_safety=factor_of_safety,
            shape=shape,
            phi_deg=phi_deg,
            cohesion=cohesion,
            unit_weight=unit_weight,
            depth=depth,
            width=width,
        )

    def meyerhof(
        self,
        cohesion: float,
        unit_weight: float,
        depth: float,
        width: float,
        phi_deg: float,
        shape: FoundationShape = FoundationShape.STRIP,
        factor_of_safety: float = 3.0,
        length: Optional[float] = None,
        load_inclination_deg: float = 0.0,
    ) -> BearingCapacityResult:
        """
        Compute bearing capacity using Meyerhof's (1963) general equation.

        qu = c·Nc·Fcs·Fcd·Fci + q·Nq·Fqs·Fqd·Fqi + 0.5·γ·B·Nγ·Fγs·Fγd·Fγi

        Args:
            cohesion: Soil cohesion c (kPa).
            unit_weight: Soil unit weight γ (kN/m³).
            depth: Foundation depth Df (m).
            width: Foundation width B (m).
            phi_deg: Soil internal friction angle φ (degrees).
            shape: Foundation shape.
            factor_of_safety: Desired factor of safety (default 3.0).
            length: Foundation length L (m); required for rectangular shape.
            load_inclination_deg: Inclination of the resultant load from
                                   vertical (degrees, default 0).

        Returns:
            BearingCapacityResult with ultimate and allowable capacities.

        Raises:
            ValueError: If input values are invalid.
        """
        self._validate_inputs(cohesion, unit_weight, depth, width, phi_deg, factor_of_safety)
        if shape == FoundationShape.RECTANGULAR and length is None:
            raise ValueError("Length must be provided for rectangular foundations.")
        if not (0 <= load_inclination_deg < 90):
            raise ValueError("Load inclination must be in [0, 90) degrees.")

        phi = math.radians(phi_deg)
        beta = math.radians(load_inclination_deg)
        nc, nq, ng = self._meyerhof_factors(phi)
        fcs, fqs, fgs = self._meyerhof_shape(phi, shape, width, length)
        fcd, fqd, fgd = self._meyerhof_depth(phi, depth, width)
        fci, fqi, fgi = self._meyerhof_inclination(beta)

        q = unit_weight * depth
        qu = (
            cohesion * nc * fcs * fcd * fci
            + q * nq * fqs * fqd * fqi
            + 0.5 * unit_weight * width * ng * fgs * fgd * fgi
        )
        qa = qu / factor_of_safety

        return BearingCapacityResult(
            method="Meyerhof (1963)",
            ultimate_bearing_capacity=qu,
            allowable_bearing_capacity=qa,
            factor_of_safety=factor_of_safety,
            shape=shape,
            phi_deg=phi_deg,
            cohesion=cohesion,
            unit_weight=unit_weight,
            depth=depth,
            width=width,
        )

    @staticmethod
    def _terzaghi_factors(phi: float) -> tuple:
        """Terzaghi bearing capacity factors Nc, Nq, Nγ."""
        if phi == 0:
            nq = 1.0
            nc = 5.7
            ng = 0.0
        else:
            nq = math.exp(math.pi * math.tan(phi)) * (math.tan(math.pi / 4 + phi / 2) ** 2)
            nc = (nq - 1) / math.tan(phi)
            ng = (nq - 1) * math.tan(1.4 * phi)
        return nc, nq, ng

    @staticmethod
    def _terzaghi_shape(
        shape: FoundationShape, width: float, length: Optional[float]
    ) -> tuple:
        """Terzaghi shape factors sc, sq, sγ."""
        if shape == FoundationShape.STRIP:
            return 1.0, 1.0, 1.0
        if shape in (FoundationShape.SQUARE, FoundationShape.CIRCULAR):
            return 1.3, 1.0, 0.8
        # Rectangular
        ratio = width / length if length else 0.0
        sc = 1 + 0.3 * ratio
        sq = 1.0
        sg = 1 - 0.2 * ratio
        return sc, sq, sg

    @staticmethod
    def _meyerhof_factors(phi: float) -> tuple:
        """Meyerhof bearing capacity factors Nc, Nq, Nγ."""
        if phi == 0:
            return 5.14, 1.0, 0.0
        nq = math.exp(math.pi * math.tan(phi)) * (math.tan(math.pi / 4 + phi / 2) ** 2)
        nc = (nq - 1) / math.tan(phi)
        ng = (nq - 1) * math.tan(phi)
        return nc, nq, ng

    @staticmethod
    def _meyerhof_shape(
        phi: float, shape: FoundationShape, width: float, length: Optional[float]
    ) -> tuple:
        """Meyerhof shape factors Fcs, Fqs, Fγs."""
        if shape == FoundationShape.STRIP:
            return 1.0, 1.0, 1.0
        if shape == FoundationShape.SQUARE:
            ratio = 1.0
        elif shape == FoundationShape.CIRCULAR:
            ratio = 1.0
        else:
            ratio = width / length if length else 1.0
        nq_nc = math.tan(phi) if phi > 0 else 0.0
        fcs = 1 + (ratio) * (nq_nc if phi > 0 else 0.2)
        fqs = 1 + ratio * math.tan(phi)
        fgs = 1 - 0.4 * ratio
        return fcs, fqs, max(0.0, fgs)

    @staticmethod
    def _meyerhof_depth(phi: float, depth: float, width: float) -> tuple:
        """Meyerhof depth factors Fcd, Fqd, Fγd."""
        ratio = depth / width if width > 0 else 0.0
        if phi == 0:
            fcd = 1 + 0.4 * ratio
            return fcd, 1.0, 1.0
        k = math.atan(ratio) if ratio > 1 else ratio
        fqd = 1 + 2 * math.tan(phi) * (1 - math.sin(phi)) ** 2 * k
        fcd = fqd - (1 - fqd) / (math.tan(phi) * 5.14) if phi > 0 else 1 + 0.4 * ratio
        fgd = 1.0
        return fcd, fqd, fgd

    @staticmethod
    def _meyerhof_inclination(beta: float) -> tuple:
        """Meyerhof inclination factors Fci, Fqi, Fγi."""
        beta_deg = math.degrees(beta)
        fqi = (1 - beta_deg / 90) ** 2
        fci = fqi
        fgi = (1 - beta_deg / 30) ** 2 if beta_deg < 30 else 0.0
        return fci, fqi, fgi

    @staticmethod
    def _validate_inputs(
        cohesion: float,
        unit_weight: float,
        depth: float,
        width: float,
        phi_deg: float,
        factor_of_safety: float,
    ) -> None:
        """Validate bearing capacity input parameters."""
        if cohesion < 0:
            raise ValueError(f"Cohesion must be >= 0, got {cohesion}.")
        if unit_weight <= 0:
            raise ValueError(f"Unit weight must be > 0, got {unit_weight}.")
        if depth < 0:
            raise ValueError(f"Foundation depth must be >= 0, got {depth}.")
        if width <= 0:
            raise ValueError(f"Foundation width must be > 0, got {width}.")
        if not (0 <= phi_deg < 90):
            raise ValueError(
                f"Friction angle must be in [0, 90) degrees, got {phi_deg}."
            )
        if factor_of_safety <= 0:
            raise ValueError(f"Factor of safety must be > 0, got {factor_of_safety}.")
