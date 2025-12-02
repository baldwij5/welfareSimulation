# Welfare Simulation with Bureaucracy Navigation Points

Agent-based simulation of welfare benefit administration using real Census data. Models how structural inequality creates disparities through administrative processes.

[![Tests](https://img.shields.io/badge/tests-107%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## Features

- **Real Census Data**: CPS ASEC 2022 (152,732 people) + ACS 2022 (3,202 counties)
- **Stratified Sampling**: Perfect demographic matching to county-level data
- **Bureaucracy Navigation Points**: Novel system modeling structural inequality
- **Complexity-Based Processing**: Applications have difficulty scores (0.3-1.0)
- **Population-Scaled Capacity**: Staff capacity scales with county population
- **AI Interventions**: Test efficiency vs equity trade-offs
- **Matched-Pairs Design**: Rigorous causal inference experiments
- **107+ Comprehensive Tests**: Full test coverage

## Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/welfareSimulation.git
cd welfareSimulation

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v
# Expected: 107+ passing

# Run demo
python demo_real_data.py
```

## Example Usage

```python
from simulation.runner import run_simulation_with_real_data
from ai.application_sorter import AI_ApplicationSorter

# Run simulation with real data
results = run_simulation_with_real_data(
    cps_file='src/data/cps_asec_2022_processed_full.csv',
    acs_file='src/data/us_census_acs_2022_county_data.csv',
    n_seekers=1000,
    n_months=24,
    counties=['Kings County, New York', 'Cook County, Illinois'],
    random_seed=42
)

# With AI intervention
ai_tool = AI_ApplicationSorter(strategy='simple_first')
results_ai = run_simulation_with_real_data(..., ai_sorter=ai_tool)

# Analyze results
print(f"Approval rate: {results['summary']['approval_rate']:.1%}")
print(f"Applications: {results['summary']['total_applications']}")
```

## Key Innovation: Bureaucracy Navigation Points

Models how structural factors affect ability to navigate administrative processes:

```python
# Each seeker has navigation capacity
seeker.bureaucracy_navigation_points  # 0-20

# Based on:
# - Education: College (+5), Less than HS (-3)
# - Employment: Employed (+3), Unemployed (-2)
# - Age: Experienced (+2), Young (-1)

# Investigation costs points
# - Basic checks: 2-3 points
# - Intensive checks: 4-6 points
# - Fraudsters pay DOUBLE

# When points < 0 → Fraud detected
```

**Result:** Disparities emerge from structural inequality, not explicit bias.

## Experiments

### Matched County-Pair Design

```bash
# Step 1: Find matched pairs
python scripts/match_counties.py

# Step 2: Run experiment
python experiments/experiment_matched_pairs.py
```

Tests whether "efficiency AI" (simple-first sorting) creates racial disparities through interaction with capacity constraints.

## Documentation

- **[Complete Documentation](docs/COMPLETE_DOCUMENTATION.md)** - Full system reference
- **[Complexity System](docs/COMPLEXITY_SYSTEM.md)** - 5-step implementation
- **[Bureaucracy Points](docs/BUREAUCRACY_POINTS.md)** - Navigation system
- **[Matched Pairs Design](docs/MATCHED_PAIRS_DESIGN.md)** - Experimental methods
- **[API Reference](docs/API_REFERENCE.md)** - Function documentation

## Testing

```bash
# All tests
pytest -v

# Specific test suite
pytest tests/test_bureaucracy_points.py -v

# With coverage
pytest --cov=src --cov-report=html
```

**Test Coverage:** 107+ tests across 8 test files
- Unit tests: 85
- Integration tests: 22

## Project Structure

```
welfareSimulation/
├── src/
│   ├── core/          # Seeker, Evaluator, Reviewer, Application
│   ├── simulation/    # Simulation engine
│   ├── data/          # Data loading, CPS/ACS integration
│   └── ai/            # AI intervention tools
├── tests/             # 107+ comprehensive tests
├── experiments/       # Experimental scripts
├── scripts/           # Analysis and calibration scripts
├── demos/             # 12+ demo scripts
└── docs/              # Documentation
```

## Requirements

```
numpy>=1.24.0
pandas>=2.0.0
pytest>=7.4.0
scikit-learn>=1.3.0
scipy>=1.10.0
```

## Data

Place Census data files in `src/data/`:
- `cps_asec_2022_processed_full.csv` (CPS data)
- `us_census_acs_2022_county_data.csv` (ACS county data)

Data available from IPUMS CPS and Census Bureau.

## Research Applications

This simulation enables research on:

### 1. Algorithmic Fairness
- Do "neutral" AI tools create disparate impact?
- Efficiency vs equity trade-offs
- Context-dependent effects

### 2. Administrative Burden
- How bureaucratic requirements affect different groups
- Role of education in navigation capacity
- Documentation burden disparities

### 3. Structural Inequality
- Disparities without explicit discrimination
- Interaction of individual capacity and system constraints
- False positives for honest low-educated applicants

### 4. Policy Design
- Optimal sorting algorithms
- Capacity allocation across counties
- Application simplification impacts

## Key Results (Preliminary)

### Finding 1: Heterogeneous AI Effects

AI sorting shows context-dependent effects:
- Large counties (ample capacity): Minimal impact
- Small counties (tight capacity): Variable effects
- Overall: Not statistically significant (n=3 pairs)

### Finding 2: Bureaucracy Points Create Disparities

- Educated (15-20 points) withstand more investigation
- Less educated (5-10 points) struggle even if honest
- Creates false positives without bias

### Finding 3: Complexity Amplification

- SSI applications most complex (0.9-1.0)
- Disabled applicants face higher burden
- Structural disadvantage, not discrimination

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

MIT License - see LICENSE file

## Citation

```bibtex
@software{baldwin2024welfare,
  author = {Baldwin, Jack},
  title = {Welfare Simulation with Bureaucracy Navigation Points},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/YOUR_USERNAME/welfareSimulation}
}
```

## Acknowledgments

- CPS data from IPUMS-CPS
- ACS data from U.S. Census Bureau
- Developed for dissertation research at [Your University]

## Contact

- **Author:** Jack Baldwin
- **Institution:** [Your University]
- **Email:** [Your email]
- **Dissertation Committee:** [Committee members]

---

**Built with real data, rigorous testing, and publication-quality experimental design.** 🎓

**Ready for peer review and dissertation defense!** 🎊