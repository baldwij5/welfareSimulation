cat > README.md << 'EOF'
# Welfare Simulation with Real CPS/ACS Data

Agent-based simulation of welfare program administration using real Census data.

## Features

- **Real data integration**: Uses CPS ASEC 2022 (152,732 people) and ACS 2022 (3,202 counties)
- **Stratified sampling**: Perfect demographic matching to county-level data
- **County-program structure**: Independent evaluators and reviewers per county-program
- **Recertification schedules**: SNAP (6mo), TANF (12mo), SSI (36mo)
- **Fraud and error mechanics**: Realistic application behaviors
- **Complete CPS variables**: All 66 variables stored per seeker for analysis

## Installation
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/welfareSimulation.git
cd welfareSimulation

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start
```python
from simulation.runner import run_simulation_with_real_data

# Run simulation with real data
results = run_simulation_with_real_data(
    cps_file='src/data/cps_asec_2022_processed_full.csv',
    acs_file='src/data/us_census_acs_2022_county_data.csv',
    n_seekers=1000,
    n_months=24,
    counties=['Kings County, New York', 'Cook County, Illinois'],
    random_seed=42
)

# Analyze results
print(f"Applications: {results['summary']['total_applications']}")
print(f"Approval rate: {results['summary']['approval_rate']:.1%}")
```

## Testing
```bash
pytest -v
```

All 65 tests should pass.

## Project Structure