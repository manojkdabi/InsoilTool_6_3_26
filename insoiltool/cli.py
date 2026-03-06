"""
InsoilTool Command-Line Interface

Entry point for running soil analysis from the command line.
"""

import argparse
import sys

from . import __version__
from .atterberg import AtterbergLimits
from .bearing_capacity import BearingCapacity, FoundationShape
from .classification import SoilClassifier
from .grain_size import GrainSizeDistribution


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for InsoilTool CLI."""
    parser = argparse.ArgumentParser(
        prog="insoiltool",
        description=f"InsoilTool v{__version__} — Soil Analysis and Classification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # USCS classification (coarse-grained, clean gravel)
  insoiltool classify-uscs --gravel 60 --sand 35 --fines 5 --cu 8 --cc 2.1

  # USCS classification (fine-grained clay)
  insoiltool classify-uscs --gravel 5 --sand 15 --fines 80 --ll 55 --pi 28

  # AASHTO classification
  insoiltool classify-aashto --p10 85 --p40 60 --p200 30 --ll 35 --pi 8

  # Atterberg limits
  insoiltool atterberg --ll 45 --pl 22 --wn 35

  # Grain size distribution
  insoiltool grainsize --data "75,100 19,85 4.75,60 2,48 0.425,32 0.075,12"

  # Bearing capacity (Terzaghi)
  insoiltool bearing --method terzaghi --c 20 --gamma 18 --df 1.5 --b 2.0 --phi 30

  # Bearing capacity (Meyerhof, square footing)
  insoiltool bearing --method meyerhof --c 10 --gamma 19 --df 1.0 --b 1.5 --phi 25 --shape square
""",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- classify-uscs ---
    p_uscs = subparsers.add_parser(
        "classify-uscs",
        help="Classify soil using Unified Soil Classification System (USCS/ASTM D2487)",
    )
    p_uscs.add_argument("--gravel", type=float, required=True, help="Percent gravel (%%)")
    p_uscs.add_argument("--sand", type=float, required=True, help="Percent sand (%%)")
    p_uscs.add_argument("--fines", type=float, required=True, help="Percent fines (%%)")
    p_uscs.add_argument("--ll", type=float, default=None, help="Liquid limit (%%)")
    p_uscs.add_argument("--pi", type=float, default=None, help="Plasticity index (%%)")
    p_uscs.add_argument("--cu", type=float, default=None, help="Coefficient of uniformity")
    p_uscs.add_argument("--cc", type=float, default=None, help="Coefficient of curvature")

    # --- classify-aashto ---
    p_aashto = subparsers.add_parser(
        "classify-aashto",
        help="Classify soil using AASHTO classification (AASHTO M 145)",
    )
    p_aashto.add_argument(
        "--p10", type=float, required=True, help="Percent passing No. 10 sieve (%%)"
    )
    p_aashto.add_argument(
        "--p40", type=float, required=True, help="Percent passing No. 40 sieve (%%)"
    )
    p_aashto.add_argument(
        "--p200", type=float, required=True, help="Percent passing No. 200 sieve (%%)"
    )
    p_aashto.add_argument("--ll", type=float, default=None, help="Liquid limit (%%)")
    p_aashto.add_argument("--pi", type=float, default=None, help="Plasticity index (%%)")

    # --- atterberg ---
    p_att = subparsers.add_parser(
        "atterberg",
        help="Compute Atterberg limits and consistency indices (ASTM D4318)",
    )
    p_att.add_argument("--ll", type=float, required=True, help="Liquid limit (%%)")
    p_att.add_argument("--pl", type=float, required=True, help="Plastic limit (%%)")
    p_att.add_argument(
        "--wn", type=float, default=None, help="Natural water content (%%) [optional]"
    )
    p_att.add_argument(
        "--sl", type=float, default=None, help="Shrinkage limit (%%) [optional]"
    )
    p_att.add_argument(
        "--clay-pct",
        type=float,
        default=None,
        help="Percent clay-sized particles for activity [optional]",
    )

    # --- grainsize ---
    p_gs = subparsers.add_parser(
        "grainsize",
        help="Analyze grain size distribution (ASTM D422/D6913)",
    )
    p_gs.add_argument(
        "--data",
        type=str,
        required=True,
        help=(
            "Grain size data as space-separated 'size,percent' pairs "
            "(e.g. '75,100 19,85 4.75,60 0.075,12')"
        ),
    )

    # --- bearing ---
    p_bc = subparsers.add_parser(
        "bearing",
        help="Calculate shallow foundation bearing capacity",
    )
    p_bc.add_argument(
        "--method",
        choices=["terzaghi", "meyerhof"],
        default="terzaghi",
        help="Calculation method (default: terzaghi)",
    )
    p_bc.add_argument("--c", type=float, required=True, help="Cohesion (kPa)")
    p_bc.add_argument("--gamma", type=float, required=True, help="Unit weight (kN/m³)")
    p_bc.add_argument("--df", type=float, required=True, help="Foundation depth (m)")
    p_bc.add_argument("--b", type=float, required=True, help="Foundation width (m)")
    p_bc.add_argument(
        "--phi", type=float, required=True, help="Friction angle (degrees)"
    )
    p_bc.add_argument(
        "--shape",
        choices=["strip", "square", "circular", "rectangular"],
        default="strip",
        help="Foundation shape (default: strip)",
    )
    p_bc.add_argument(
        "--length", type=float, default=None, help="Foundation length L (m); required for rectangular"
    )
    p_bc.add_argument(
        "--fs", type=float, default=3.0, help="Factor of safety (default: 3.0)"
    )
    p_bc.add_argument(
        "--inclination",
        type=float,
        default=0.0,
        help="Load inclination from vertical (degrees, Meyerhof only)",
    )

    return parser


def cmd_classify_uscs(args: argparse.Namespace) -> int:
    """Handle classify-uscs command."""
    try:
        classifier = SoilClassifier()
        result = classifier.classify_uscs(
            percent_gravel=args.gravel,
            percent_sand=args.sand,
            percent_fines=args.fines,
            liquid_limit=args.ll,
            plasticity_index=args.pi,
            cu=args.cu,
            cc=args.cc,
        )
        print("\nUSCS Classification Result")
        print("=" * 40)
        print(result)
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_classify_aashto(args: argparse.Namespace) -> int:
    """Handle classify-aashto command."""
    try:
        classifier = SoilClassifier()
        result = classifier.classify_aashto(
            percent_passing_no10=args.p10,
            percent_passing_no40=args.p40,
            percent_passing_no200=args.p200,
            liquid_limit=args.ll,
            plasticity_index=args.pi,
        )
        print("\nAASHTO Classification Result")
        print("=" * 40)
        print(result)
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_atterberg(args: argparse.Namespace) -> int:
    """Handle atterberg command."""
    try:
        al = AtterbergLimits()
        result = al.compute(
            liquid_limit=args.ll,
            plastic_limit=args.pl,
            natural_water_content=args.wn,
            shrinkage_limit=args.sl,
        )
        print("\nAtterberg Limits Analysis")
        print("=" * 40)
        print(result)

        pi = result.plasticity_index
        print(f"\nPlasticity description:  {al.describe_plasticity(pi)}")

        if result.liquidity_index is not None:
            print(
                f"Consistency description: {al.describe_consistency(result.liquidity_index)}"
            )

        if args.clay_pct is not None:
            activity = al.activity(pi, args.clay_pct)
            print(f"Activity (A = PI/clay%): {activity:.3f}")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_grainsize(args: argparse.Namespace) -> int:
    """Handle grainsize command."""
    try:
        data = _parse_grainsize_data(args.data)
        gs = GrainSizeDistribution()
        result = gs.analyze(data)
        print("\nGrain Size Distribution Analysis")
        print("=" * 40)
        print(result)
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _parse_grainsize_data(raw: str):
    """Parse grain size data string into list of (size, percent) tuples."""
    pairs = []
    for token in raw.split():
        token = token.strip()
        if not token:
            continue
        parts = token.split(",")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid data point '{token}': expected 'size,percent' format."
            )
        try:
            size = float(parts[0])
            percent = float(parts[1])
        except ValueError:
            raise ValueError(
                f"Invalid numeric value in '{token}'."
            )
        pairs.append((size, percent))
    if not pairs:
        raise ValueError("No grain size data points provided.")
    return pairs


def cmd_bearing(args: argparse.Namespace) -> int:
    """Handle bearing command."""
    try:
        shape = FoundationShape(args.shape)
        bc = BearingCapacity()
        if args.method == "terzaghi":
            result = bc.terzaghi(
                cohesion=args.c,
                unit_weight=args.gamma,
                depth=args.df,
                width=args.b,
                phi_deg=args.phi,
                shape=shape,
                factor_of_safety=args.fs,
                length=args.length,
            )
        else:
            result = bc.meyerhof(
                cohesion=args.c,
                unit_weight=args.gamma,
                depth=args.df,
                width=args.b,
                phi_deg=args.phi,
                shape=shape,
                factor_of_safety=args.fs,
                length=args.length,
                load_inclination_deg=args.inclination,
            )
        print("\nBearing Capacity Analysis")
        print("=" * 40)
        print(result)
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    """Main entry point for InsoilTool CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "classify-uscs": cmd_classify_uscs,
        "classify-aashto": cmd_classify_aashto,
        "atterberg": cmd_atterberg,
        "grainsize": cmd_grainsize,
        "bearing": cmd_bearing,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
