"""
Demo: Step 2 - Population-Based Capacity

Shows how staff capacity scales with county population.
Run with: python demo_capacity_step2.py
"""

import sys
sys.path.insert(0, 'src')

from simulation.runner import run_simulation_with_real_data, calculate_evaluator_capacity, calculate_reviewer_capacity
from data.data_loader import load_acs_county_data


def demo_capacity_calculation():
    """Show how capacity is calculated from population."""
    print("=" * 70)
    print("CAPACITY CALCULATION BY COUNTY POPULATION")
    print("=" * 70)
    
    # Load ACS to get real populations
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Select diverse counties
    counties = [
        'Loving County, Texas',           # Smallest (~100 people)
        'Autauga County, Alabama',        # Small (~59k)
        'Baldwin County, Alabama',        # Medium (~233k)
        'Kings County, New York',         # Large (~2.7M)
        'Los Angeles County, California'  # Largest (~10M)
    ]
    
    print("\nStaff capacity by county size:\n")
    print(f"  {'County':<35} | {'Population':>12} | {'Eval Cap':>10} | {'Review Cap':>11}")
    print(f"  {'-'*35}-+-{'-'*12}-+-{'-'*10}-+-{'-'*11}")
    
    for county_name in counties:
        county_data = acs[acs['county_name'] == county_name]
        if len(county_data) > 0:
            pop = county_data.iloc[0]['total_county_population']
            eval_cap = calculate_evaluator_capacity(pop)
            rev_cap = calculate_reviewer_capacity(pop)
            
            print(f"  {county_name:<35} | {pop:>12,} | {eval_cap:>9.1f}u | {rev_cap:>10.1f}u")
    
    print(f"\n  u = complexity units per month")
    print(f"\nKey insight: Larger counties have more staff capacity!")


def demo_staff_ratios():
    """Show the staff-to-population ratios."""
    print("\n" + "=" * 70)
    print("STAFF RATIOS")
    print("=" * 70)
    
    print("\nDefault ratios:")
    print("  Evaluators: 1 staff per 50,000 people")
    print("    → Each staff handles 20 complexity units/month")
    print("\n  Reviewers: 1 staff per 100,000 people (more specialized)")
    print("    → Each staff handles 10 complexity units/month")
    
    print("\nExamples:")
    
    examples = [
        ("Small county", 50000),
        ("Medium county", 500000),
        ("Large county", 2500000)
    ]
    
    for name, pop in examples:
        eval_staff = pop / 50000
        eval_cap = eval_staff * 20
        rev_staff = pop / 100000
        rev_cap = rev_staff * 10
        
        print(f"\n  {name} ({pop:,} people):")
        print(f"    Evaluators: {eval_staff:.1f} staff = {eval_cap:.0f} units/month")
        print(f"    Reviewers: {rev_staff:.1f} staff = {rev_cap:.0f} units/month")


def demo_real_simulation():
    """Run simulation with population-based capacity."""
    print("\n" + "=" * 70)
    print("SIMULATION WITH POPULATION-BASED CAPACITY")
    print("=" * 70)
    
    counties = [
        'Autauga County, Alabama',      # Pop: 58,761
        'Baldwin County, Alabama',      # Pop: 233,420
        'Jefferson County, Alabama'     # Pop: 658,573
    ]
    
    print(f"\nRunning simulation with 3 counties of different sizes...")
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=300,  # 100 per county
        n_months=6,
        counties=counties,
        random_seed=42
    )
    
    print(f"\n\nResults by county:")
    for county in counties:
        county_seekers = [s for s in results['seekers'] if s.county == county]
        apps = sum(s.num_applications for s in county_seekers)
        
        # Get capacity
        eval_cap = results['evaluators'][(county, 'SNAP')].monthly_capacity
        rev_cap = results['reviewers'][(county, 'SNAP')].monthly_capacity
        
        print(f"\n  {county}:")
        print(f"    Seekers: {len(county_seekers)}")
        print(f"    Applications: {apps}")
        print(f"    Evaluator capacity: {eval_cap:.1f} units/month")
        print(f"    Reviewer capacity: {rev_cap:.1f} units/month")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Step 2: Population-Based Capacity")
    print("="*70)
    print("\nStaff capacity now scales with county population!")
    print("\nFormula:")
    print("  Evaluators: (population / 50,000) × 20 units")
    print("  Reviewers: (population / 100,000) × 10 units")
    print("\nResult: Large counties can process more applications!")
    
    demo_capacity_calculation()
    demo_staff_ratios()
    demo_real_simulation()
    
    print("\n" + "="*70)
    print("Step 2 Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  ✓ Capacity scales with county population")
    print("  ✓ Small counties: ~10-20 units/month")
    print("  ✓ Large counties: ~500-1000 units/month")
    print("  ✓ Realistic staffing levels!")
    print("\nNext: Step 3 - Add capacity tracking to Evaluator")


if __name__ == "__main__":
    main()