"""
Quick test of calibration with warnings suppressed
"""

import warnings
warnings.filterwarnings('ignore', message='X does not have valid feature names')

import sys
sys.path.insert(0, 'src')

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month

print("=" * 70)
print("QUICK CALIBRATION TEST (warnings suppressed)")
print("=" * 70)

# Get MA counties
print("\nLoading counties...")
acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
acs['state'] = acs['county_name'].str.split(', ').str[1]
ma_counties = acs[acs['state'] == 'Massachusetts']['county_name'].tolist()
print(f"✓ Found {len(ma_counties)} MA counties")

# Create small population (just 1000 to test fast)
print("\nCreating test population (1,000 seekers)...")
seekers = create_realistic_population(
    cps_file='src/data/cps_asec_2022_processed_full.csv',
    acs_file='src/data/us_census_acs_2022_county_data.csv',
    n_seekers=1000,
    counties=ma_counties,
    proportional=True,
    random_seed=42
)
print(f"✓ Created {len(seekers)} seekers")

# Create staff
print("\nCreating staff...")
evaluators = create_evaluators(ma_counties, acs_data=acs, random_seed=42)
reviewers = create_reviewers(ma_counties, acs_data=acs, load_state_models=True, random_seed=42)

print(f"✓ Evaluators type: {type(evaluators)}")
print(f"✓ Evaluators count: {len(evaluators)}")
print(f"✓ Reviewers type: {type(reviewers)}")
print(f"✓ Reviewers count: {len(reviewers)}")

# Apply capacity multiplier
capacity_mult = 1.0
print(f"\nApplying capacity multiplier: {capacity_mult}...")

applied_eval = 0
for key, evaluator in evaluators.items():
    if hasattr(evaluator, 'monthly_capacity'):
        original = evaluator.monthly_capacity
        evaluator.monthly_capacity *= capacity_mult
        applied_eval += 1
        if applied_eval == 1:  # Show first one as example
            print(f"  Example evaluator capacity: {original} → {evaluator.monthly_capacity}")

applied_rev = 0
for key, reviewer in reviewers.items():
    if hasattr(reviewer, 'monthly_capacity'):
        reviewer.monthly_capacity *= capacity_mult
        applied_rev += 1

print(f"✓ Applied to {applied_eval}/{len(evaluators)} evaluators")
print(f"✓ Applied to {applied_rev}/{len(reviewers)} reviewers")

# Run simulation
print("\nRunning 12 months...")
try:
    for month in range(12):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=None)
        if month == 0:
            print(f"  Month {month}: ✓")
        elif month == 11:
            print(f"  Month {month}: ✓")
    print("✓ Simulation complete")
except Exception as e:
    print(f"✗ Simulation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Count enrollment
def count_enrolled(seekers, program):
    return sum(1 for s in seekers if program in s.enrolled_programs)

tanf = count_enrolled(seekers, 'TANF')
snap = count_enrolled(seekers, 'SNAP')
ssi = count_enrolled(seekers, 'SSI')

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)
print(f"TANF enrollment: {tanf:,}")
print(f"SNAP enrollment: {snap:,}")
print(f"SSI enrollment:  {ssi:,}")
print("\n✅ TEST SUCCESSFUL!")
print("\nThe calibration script should work now.")
print("Run with warnings suppressed:")
print("  python scripts/calibrate_massachusetts_v4.py")