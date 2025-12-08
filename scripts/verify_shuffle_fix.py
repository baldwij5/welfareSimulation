"""
Verify the shuffle fix works - race order should now vary across seeds
"""

import sys
sys.path.insert(0, 'src')

from data.data_loader import create_realistic_population

counties = ['Suffolk County, Massachusetts']

print("="*70)
print("TESTING SHUFFLE FIX")
print("="*70)

# Create 3 populations with different seeds
pop1 = create_realistic_population(
    'src/data/cps_asec_2022_processed_full.csv',
    'src/data/us_census_acs_2022_county_data.csv',
    100,
    counties,
    True,
    42
)

pop2 = create_realistic_population(
    'src/data/cps_asec_2022_processed_full.csv',
    'src/data/us_census_acs_2022_county_data.csv',
    100,
    counties,
    True,
    43
)

# Check IDs (should differ)
ids1 = [s.id for s in pop1[:10]]
ids2 = [s.id for s in pop2[:10]]

print(f"\nPop1 first 10 IDs: {ids1}")
print(f"Pop2 first 10 IDs: {ids2}")
print(f"IDs differ: {ids1 != ids2}")

# Check races (should NOW differ after shuffle!)
races1 = [s.race for s in pop1]
races2 = [s.race for s in pop2]

print(f"\nPop1 first 10 races: {races1[:10]}")
print(f"Pop2 first 10 races: {races2[:10]}")

races_identical = (races1 == races2)
print(f"\nRaces identical: {races_identical}")

if races_identical:
    print("❌ SHUFFLE NOT WORKING - races still in same order!")
else:
    print("✓ SHUFFLE WORKING - race order randomized!")
    
    # Count how many positions differ
    diffs = sum(1 for r1, r2 in zip(races1, races2) if r1 != r2)
    print(f"  Positions with different races: {diffs}/100")
    
    # Check incomes vary
    import numpy as np
    incomes1 = [s.income for s in pop1]
    incomes2 = [s.income for s in pop2]
    corr = np.corrcoef(incomes1, incomes2)[0,1]
    
    print(f"  Income correlation: {corr:.4f}")
    
    if abs(corr) < 0.1:
        print(f"\n✅ FULL FIX VERIFIED!")
        print(f"   - IDs differ (unique ranges)")
        print(f"   - Races differ (shuffle working)")
        print(f"   - Incomes uncorrelated (sampling working)")
        print(f"\n   Monte Carlo will now have REAL variance!")
    else:
        print(f"\n⚠️  Income correlation unexpectedly high: {corr:.2f}")