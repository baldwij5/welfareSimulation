"""
Diagnostic: Check if seeker IDs are truly unique across seeds

This will confirm whether the variance bug is due to identical IDs.
"""

import sys
sys.path.insert(0, 'src')

from data.data_loader import create_realistic_population

county = ['Suffolk County, Massachusetts']

print("="*70)
print("SEEKER ID DIAGNOSTIC")
print("="*70)

# Create 3 populations with different seeds
populations = {}
for seed in [42, 43, 44]:
    print(f"\nCreating population with seed={seed}...")
    pop = create_realistic_population(
        'src/data/cps_asec_2022_processed_full.csv',
        'src/data/us_census_acs_2022_county_data.csv',
        n_seekers=100,
        counties=county,
        proportional=True,
        random_seed=seed
    )
    populations[seed] = pop
    
    # Show first 10 seeker IDs
    ids = [s.id for s in pop[:10]]
    races = [s.race for s in pop[:10]]
    incomes = [s.income for s in pop[:10]]
    
    print(f"  First 10 IDs: {ids}")
    print(f"  First 10 races: {races}")
    print(f"  First 10 incomes: {[f'${x:,.0f}' for x in incomes]}")

# Compare IDs across seeds
print(f"\n{'='*70}")
print("COMPARISON")
print("="*70)

ids_42 = [s.id for s in populations[42]]
ids_43 = [s.id for s in populations[43]]
ids_44 = [s.id for s in populations[44]]

print(f"\nSeed 42 IDs: {ids_42[:10]}...")
print(f"Seed 43 IDs: {ids_43[:10]}...")
print(f"Seed 44 IDs: {ids_44[:10]}...")

if ids_42 == ids_43 == ids_44:
    print(f"\n❌ CRITICAL BUG CONFIRMED!")
    print(f"   All seeds produce IDENTICAL IDs")
    print(f"   IDs are: {list(range(100))}")
    print(f"\n   This means:")
    print(f"   - All Monte Carlo iterations use same seekers")
    print(f"   - Your -11.35pp result is from ~1 sample, not 20!")
    print(f"   - The t=-535 and CI=0.08pp make sense now (no variance!)")
    print(f"\n   FIX REQUIRED:")
    print(f"   - Seeker IDs must incorporate random element")
    print(f"   - Or use actual CPS row index (unique per sample)")
else:
    print(f"\n✓ Seeker IDs are different across seeds")
    print(f"   The variance issue is elsewhere")

# Check if actual seekers differ despite same IDs
races_42 = [s.race for s in populations[42]]
races_43 = [s.race for s in populations[43]]

if ids_42 == ids_43:
    print(f"\nDo seekers differ in CHARACTERISTICS despite same IDs?")
    
    different_races = sum(1 for r1, r2 in zip(races_42, races_43) if r1 != r2)
    print(f"  Seekers with different races: {different_races}/100")
    
    if different_races > 0:
        print(f"  → Sampling IS working, but IDs are wrong")
        print(f"  → In parallel worlds, you're comparing DIFFERENT people")
        print(f"  → But seeker_dict lookup finds WRONG seekers!")
    else:
        print(f"  → Even characteristics are identical")
        print(f"  → Seeds completely not working")

print(f"\n{'='*70}")