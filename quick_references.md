# Quick Reference Guide - Welfare Simulation

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/welfareSimulation.git
cd welfareSimulation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -v  # Should show 111 passing
```

---

## Running Simulations

### Basic Simulation

```python
from simulation.runner import run_simulation_with_real_data

results = run_simulation_with_real_data(
    cps_file='src/data/cps_asec_2022_processed_full.csv',
    acs_file='src/data/us_census_acs_2022_county_data.csv',
    n_seekers=500,
    n_months=12,
    counties=['Jefferson County, Alabama'],
    random_seed=42
)
```

### With AI Intervention

```python
from ai.application_sorter import AI_ApplicationSorter

ai = AI_ApplicationSorter(strategy='simple_first')
results = run_simulation_with_real_data(..., ai_sorter=ai)
```

---

## Analyzing Results

### Racial Disparities

```python
white = [s for s in results['seekers'] if s.race == 'White']
black = [s for s in results['seekers'] if s.race == 'Black']

white_rate = sum(s.num_approvals for s in white) / sum(s.num_applications for s in white)
black_rate = sum(s.num_approvals for s in black) / sum(s.num_applications for s in black)

gap = white_rate - black_rate
print(f"Racial disparity: {gap:.1%}")
```

### By Education

```python
college = [s for s in results['seekers'] if s.education in ['bachelors', 'graduate']]
less_ed = [s for s in results['seekers'] if s.education == 'less_than_hs']

# Compare approval rates, investigation rates, etc.
```

### By Bureaucracy Points

```python
low_points = [s for s in results['seekers'] if s.bureaucracy_navigation_points < 8]
high_points = [s for s in results['seekers'] if s.bureaucracy_navigation_points > 15]

# Compare denial rates
```

---

## Running Experiments

### Matched County-Pair Experiment

```bash
# Step 1: Find matched pairs
python scripts/match_counties.py

# Step 2: Run experiment
python experiments/experiment_matched_pairs.py
```

### Diagnostic Analysis

```bash
# Understand population differences
python scripts/diagnose_ai_results.py

# Calibrate capacity
python scripts/calibrate_capacity.py
```

---

## Key Parameters

### Complexity Scores
- SNAP: 0.30 base
- TANF: 0.50 base
- SSI: 0.70 base
- +0.20 for disability
- +0.15 for new application

### Capacity (per month)
- Evaluators: (pop/50,000) × 25 units
- Reviewers: (pop/50,000) × 15 units

### Bureaucracy Points
- Base: 10
- College: +5
- Employed: +3
- Less than HS: -3
- Unemployed: -2

### Investigation Costs
- Basic check: 2 points
- Pay stubs: 3 points
- Interview: 4 points
- Fraud penalty: ×2

---

## Troubleshooting

### Tests Failing?
```bash
# Check imports
python -c "import src.core.seeker"

# Run specific test
pytest tests/test_core.py -v

# Check Python version
python --version  # Should be 3.12+
```

### Low Approval Rates?
- Check capacity calibration
- Increase evaluator units (25 → 30)
- Check fraud/error rates

### Import Errors?
- Ensure in project root
- Check PYTHONPATH
- Verify folder structure

---

## File Locations

### Core Code
- `src/core/` - Seeker, Application, Evaluator, Reviewer
- `src/simulation/` - Simulation engine
- `src/data/` - Data loading
- `src/ai/` - AI tools

### Tests
- `tests/` - 111 comprehensive tests
- Run: `pytest -v`

### Experiments
- `experiments/` - Experimental scripts
- `scripts/` - Analysis tools

### Data
- `src/data/` - Census data files
- `data/` - Generated files (matched pairs)

---

## Common Tasks

### Export Results to CSV

```python
import pandas as pd

# Create seeker-level dataset
data = []
for seeker in results['seekers']:
    data.append({
        'seeker_id': seeker.id,
        'race': seeker.race,
        'income': seeker.income,
        'education': seeker.education,
        'bureaucracy_points': seeker.bureaucracy_navigation_points,
        'applications': seeker.num_applications,
        'approvals': seeker.num_approvals,
        'denials': seeker.num_denials,
        'investigations': seeker.num_investigations
    })

df = pd.DataFrame(data)
df.to_csv('results/seeker_outcomes.csv', index=False)
```

### Run Multiple Counties

```python
counties = [
    'Kings County, New York',
    'Cook County, Illinois', 
    'Los Angeles County, California',
    'Harris County, Texas'
]

results = run_simulation_with_real_data(
    ...,
    n_seekers=2000,  # 500 per county
    counties=counties
)
```

---

## Contact & Support

**Issues:** GitHub Issues  
**Questions:** Dissertation committee  
**Collaboration:** Fork and PR  

---

*Quick Reference v1.0 - December 2024*