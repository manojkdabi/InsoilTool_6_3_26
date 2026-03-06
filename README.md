# InsoilTool 6.3.26

A soil analysis and classification command-line tool and Python library for geotechnical engineering.

## Features

- **USCS Classification** — Unified Soil Classification System (ASTM D2487): GW, GP, GM, GC, SW, SP, SM, SC, CL, CH, ML, MH, CL-ML
- **AASHTO Classification** — AASHTO M 145: A-1 through A-7 with Group Index
- **Atterberg Limits** — Plasticity index, liquidity index, consistency index, activity, plasticity/consistency descriptions
- **Grain Size Distribution** — D10, D30, D50, D60, Cu, Cc, gradation description (ASTM D422/D6913)
- **Bearing Capacity** — Ultimate and allowable capacity using Terzaghi (1943) and Meyerhof (1963) methods

## Requirements

- Python 3.9 or newer

## Installation

```bash
pip install .
```

## Usage

### Command-Line Interface

```
insoiltool --version
insoiltool --help
```

#### USCS Classification

```bash
# Well-graded gravel (clean)
insoiltool classify-uscs --gravel 65 --sand 31 --fines 4 --cu 8.0 --cc 2.1

# Lean clay
insoiltool classify-uscs --gravel 2 --sand 15 --fines 83 --ll 40 --pi 20
```

#### AASHTO Classification

```bash
insoiltool classify-aashto --p10 90 --p40 75 --p200 50 --ll 35 --pi 8
```

#### Atterberg Limits

```bash
# With natural water content and clay percentage
insoiltool atterberg --ll 45 --pl 22 --wn 35 --clay-pct 30
```

#### Grain Size Distribution

```bash
insoiltool grainsize --data "75,100 19,85 4.75,60 2,45 0.425,28 0.075,10"
```

Data format: space-separated `size_mm,percent_passing` pairs.

#### Bearing Capacity

```bash
# Terzaghi strip footing
insoiltool bearing --method terzaghi --c 20 --gamma 18 --df 1.5 --b 2.0 --phi 30

# Meyerhof square footing
insoiltool bearing --method meyerhof --c 10 --gamma 19 --df 1.0 --b 1.5 --phi 25 --shape square --fs 3.0
```

Available shapes: `strip`, `square`, `circular`, `rectangular` (add `--length L` for rectangular).

### Python API

```python
from insoiltool import SoilClassifier, AtterbergLimits, GrainSizeDistribution, BearingCapacity
from insoiltool.bearing_capacity import FoundationShape

# USCS classification
classifier = SoilClassifier()
result = classifier.classify_uscs(
    percent_gravel=2, percent_sand=15, percent_fines=83,
    liquid_limit=40, plasticity_index=20
)
print(result)  # CL - Lean clay (low plasticity)

# Atterberg limits
al = AtterbergLimits()
limits = al.compute(liquid_limit=45, plastic_limit=22, natural_water_content=35)
print(limits.liquidity_index)   # 0.565
print(al.describe_consistency(limits.liquidity_index))  # Soft

# Grain size distribution
gs = GrainSizeDistribution()
gsd = gs.analyze([
    (75.0, 100.0), (19.0, 85.0), (4.75, 60.0),
    (2.0, 45.0), (0.425, 28.0), (0.075, 10.0),
])
print(f"D50 = {gsd.d50:.2f} mm, Cu = {gsd.cu:.1f}")

# Bearing capacity
bc = BearingCapacity()
result = bc.meyerhof(
    cohesion=20, unit_weight=18, depth=1.5, width=2.0,
    phi_deg=30, shape=FoundationShape.SQUARE
)
print(f"Allowable bearing capacity: {result.allowable_bearing_capacity:.1f} kPa")
```

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## License

MIT
