"""
Demo: Step 3 - Evaluator Capacity Tracking

Shows evaluators using complexity-based capacity and hitting limits.
Run with: python demo_evaluator_capacity_step3.py
"""

import sys
sys.path.insert(0, 'src')

from simulation.runner import run_simulation_with_real_data


def demo_capacity_in_action():
    """Show evaluators using and exceeding capacity."""
    print("=" * 70)
    print("EVALUATOR CAPACITY IN ACTION")
    print("=" * 70)
    
    # Use a small county with limited capacity
    counties = ['Autauga County, Alabama']  # Pop: 58,761 → ~23.5 units
    
    print(f"\nRunning simulation with small county (limited capacity)...")
    print(f"  Autauga County: ~23.5 evaluator units/month")
    print(f"  With 100 seekers, might hit capacity limits!\n")
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=100,
        n_months=12,
        counties=counties,
        random_seed=42
    )
    
    print(f"\n{'='*70}")
    print(f"CAPACITY USAGE BY MONTH")
    print(f"{'='*70}\n")
    print(f"  {'Month':>5} | {'Apps':>4} | {'Approved':>8} | {'Denied':>6} | {'Exceeded':>8}")
    print(f"  {'-'*5}-+-{'-'*4}-+-{'-'*8}-+-{'-'*6}-+-{'-'*8}")
    
    for stats in results['monthly_stats']:
        print(f"  {stats['month']:>5} | {stats['applications_submitted']:>4} | "
              f"{stats['applications_approved']:>8} | {stats['applications_denied']:>6} | "
              f"{stats.get('applications_capacity_exceeded', 0):>8}")
    
    # Check evaluator capacity usage
    evaluator = results['evaluators'][('Autauga County, Alabama', 'SNAP')]
    
    print(f"\nSNAP Evaluator final status:")
    print(f"  Monthly capacity: {evaluator.monthly_capacity:.1f} units")
    print(f"  Used this month: {evaluator.capacity_used_this_month:.1f} units")
    print(f"  Remaining: {evaluator.monthly_capacity - evaluator.capacity_used_this_month:.1f} units")
    
    total_exceeded = sum(s.get('applications_capacity_exceeded', 0) for s in results['monthly_stats'])
    total_apps = results['summary']['total_applications']
    
    if total_exceeded > 0:
        print(f"\n⚠️  Capacity exceeded: {total_exceeded} applications ({total_exceeded/total_apps*100:.1f}%)")
        print(f"   → These applications were not processed (queued)")
    else:
        print(f"\n✓  No capacity issues (all applications processed)")


def demo_small_vs_large_county():
    """Compare capacity constraints in small vs large county."""
    print("\n" + "=" * 70)
    print("SMALL vs LARGE COUNTY CAPACITY")
    print("=" * 70)
    
    print(f"\nScenario: Same number of seekers (200), different county sizes\n")
    
    # Small county
    print(f"Small County (Autauga, 59k pop):")
    results_small = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=200,
        n_months=6,
        counties=['Autauga County, Alabama'],
        random_seed=42
    )
    
    exceeded_small = sum(s.get('applications_capacity_exceeded', 0) 
                        for s in results_small['monthly_stats'])
    
    print(f"  Capacity exceeded: {exceeded_small} applications")
    
    # Large county
    print(f"\nLarge County (Jefferson, 672k pop):")
    results_large = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=200,
        n_months=6,
        counties=['Jefferson County, Alabama'],
        random_seed=42
    )
    
    exceeded_large = sum(s.get('applications_capacity_exceeded', 0) 
                        for s in results_large['monthly_stats'])
    
    print(f"  Capacity exceeded: {exceeded_large} applications")
    
    print(f"\n→ Large county has {exceeded_small - exceeded_large} fewer overflows!")
    print(f"  (More staff capacity handles same workload better)")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Step 3: Evaluator Capacity Tracking")
    print("="*70)
    print("\nEvaluators now:")
    print("  • Track complexity units used each month")
    print("  • Check capacity before processing")
    print("  • Return CAPACITY_EXCEEDED if overloaded")
    print("\nResult: Realistic capacity constraints!")
    
    demo_capacity_in_action()
    demo_small_vs_large_county()
    
    print("\n" + "="*70)
    print("Step 3 Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  ✓ Evaluators track capacity usage")
    print("  ✓ Applications can exceed capacity")
    print("  ✓ Small counties more likely to hit limits")
    print("  ✓ Capacity scales with population")
    print("\nNext: Step 4 - Add capacity tracking to Reviewer")


if __name__ == "__main__":
    main()