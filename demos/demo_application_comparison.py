"""
Demo: Equal vs Proportional Allocation

Shows how seeker distribution differs between methods.
Run with: python demo_allocation_comparison.py
"""

import sys
sys.path.insert(0, 'src')

from data.data_loader import create_realistic_population


def demo_allocations():
    """Compare equal vs proportional allocation."""
    print("=" * 70)
    print("EQUAL vs PROPORTIONAL ALLOCATION")
    print("=" * 70)
    
    counties = [
        'Jefferson County, Alabama',
        'Kings County, New York',
        'Cook County, Illinois',
        'Maricopa County, Arizona',
        'Orange County, California',
        'Harris County, Texas',
        'King County, Washington',
        'Fulton County, Georgia'
    ]
    
    n_seekers = 1600
    
    print(f"\nTotal seekers to allocate: {n_seekers}")
    print(f"Across {len(counties)} counties")
    
    # Method 1: Equal allocation
    print(f"\n{'='*70}")
    print("METHOD 1: EQUAL ALLOCATION")
    print(f"{'='*70}")
    print(f"\nEach county gets: {n_seekers // len(counties)} seekers")
    
    seekers_equal = create_realistic_population(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers,
        counties=counties,
        proportional=False,  # Equal
        random_seed=42
    )
    
    print(f"\n  Result: {len(seekers_equal)} seekers created")
    
    # Show distribution
    print(f"\n  Distribution by county:")
    for county in counties:
        count = sum(1 for s in seekers_equal if s.county == county)
        print(f"    {county}: {count} seekers")
    
    # Method 2: Proportional allocation
    print(f"\n{'='*70}")
    print("METHOD 2: PROPORTIONAL ALLOCATION")
    print(f"{'='*70}")
    print(f"\nAllocated by eligible population (total_pop × poverty × 2.5)")
    
    seekers_proportional = create_realistic_population(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers,
        counties=counties,
        proportional=True,  # Proportional
        random_seed=42
    )
    
    print(f"\n  Result: {len(seekers_proportional)} seekers created")
    
    # Comparison
    print(f"\n{'='*70}")
    print("COMPARISON")
    print(f"{'='*70}\n")
    
    print(f"  {'County':<35} | {'Equal':>8} | {'Proportional':>13} | {'Ratio':>7}")
    print(f"  {'-'*35}-+-{'-'*8}-+-{'-'*13}-+-{'-'*7}")
    
    for county in counties:
        equal_count = sum(1 for s in seekers_equal if s.county == county)
        prop_count = sum(1 for s in seekers_proportional if s.county == county)
        ratio = prop_count / equal_count if equal_count > 0 else 0
        
        county_short = county.split(',')[0]
        state = county.split(', ')[1]
        
        print(f"  {county_short+', '+state:<35} | {equal_count:>8} | {prop_count:>13} | {ratio:>6.2f}x")
    
    print(f"\n  → Proportional gives 0.25x to 2.6x the equal allocation")
    print(f"  → Large counties get more (reflects reality)")
    print(f"  → Small counties get less")


def main():
    """Run demo."""
    print("\n" + "="*70)
    print("Allocation Methods Comparison")
    print("="*70)
    print("\nQuestion: How should we distribute seekers across counties?")
    print("\nMethod 1 (OLD): Equal - Each county gets same number")
    print("Method 2 (NEW): Proportional - Counties get share of eligible pop")
    
    demo_allocations()
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    print("\nFor external validity (generalizing to nation):")
    print("  → Use PROPORTIONAL allocation")
    print("  → Reflects actual geographic distribution")
    print("  → Large counties weighted appropriately")
    print("\nFor internal validity (county-level effects):")
    print("  → Use EQUAL allocation")
    print("  → Each county is one observation")
    print("  → Good for heterogeneity analysis")
    print("\nBest practice: Run BOTH and compare for robustness!")


if __name__ == "__main__":
    main()