"""
Demo: Step 4 - Reviewer Capacity Tracking

Shows reviewers using complexity-based capacity.
Run with: python demo_reviewer_capacity_step4.py
"""

import sys
sys.path.insert(0, 'src')

from simulation.runner import run_simulation_with_real_data


def demo_reviewer_capacity():
    """Show reviewers hitting capacity limits."""
    print("=" * 70)
    print("REVIEWER CAPACITY IN ACTION")
    print("=" * 70)
    
    # Small county with limited reviewer capacity
    counties = ['Autauga County, Alabama']  # ~5.9 reviewer units
    
    print(f"\nSmall county with limited reviewer capacity:")
    print(f"  Autauga County: ~5.9 reviewer units/month")
    print(f"  Complex cases will hit this limit quickly!\n")
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=100,
        n_months=12,
        counties=counties,
        random_seed=42
    )
    
    print(f"\n{'='*70}")
    print(f"REVIEWER WORKLOAD")
    print(f"{'='*70}")
    
    # Get reviewer
    reviewer = results['reviewers'][('Autauga County, Alabama', 'SNAP')]
    
    print(f"\nSNAP Reviewer:")
    print(f"  Monthly capacity: {reviewer.monthly_capacity:.1f} units")
    print(f"  Applications reviewed: {reviewer.applications_reviewed}")
    print(f"  Approved: {reviewer.applications_approved}")
    print(f"  Denied: {reviewer.applications_denied}")
    print(f"  Fraud detected: {reviewer.fraud_detected}")
    
    # Check if capacity was hit
    total_escalated = sum(s['applications_escalated'] for s in results['monthly_stats'])
    print(f"\n  Total escalations across all months: {total_escalated}")
    print(f"  Reviews completed: {reviewer.applications_reviewed}")
    
    if total_escalated > reviewer.applications_reviewed:
        overflow = total_escalated - reviewer.applications_reviewed
        print(f"  ⚠️  Reviewer overflow: {overflow} cases auto-approved (capacity exceeded)")
    else:
        print(f"  ✓  All escalations reviewed (within capacity)")


def demo_small_vs_large_reviewer():
    """Compare reviewer capacity in different county sizes."""
    print("\n" + "=" * 70)
    print("SMALL vs LARGE COUNTY REVIEWERS")
    print("=" * 70)
    
    print(f"\nComparing reviewer capacity with same workload (150 seekers):\n")
    
    # Small county
    print(f"Small County (Autauga, 59k):")
    results_small = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=150,
        n_months=6,
        counties=['Autauga County, Alabama'],
        random_seed=42
    )
    
    reviewer_small = results_small['reviewers'][('Autauga County, Alabama', 'SNAP')]
    escalated_small = sum(s['applications_escalated'] for s in results_small['monthly_stats'])
    overflow_small = max(0, escalated_small - reviewer_small.applications_reviewed)
    
    print(f"  Reviewer capacity: {reviewer_small.monthly_capacity:.1f} units")
    print(f"  Escalations: {escalated_small}")
    print(f"  Reviewed: {reviewer_small.applications_reviewed}")
    print(f"  Overflow: {overflow_small} ({overflow_small/escalated_small*100:.1f}% auto-approved)")
    
    # Large county
    print(f"\nLarge County (Jefferson, 672k):")
    results_large = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=150,
        n_months=6,
        counties=['Jefferson County, Alabama'],
        random_seed=42
    )
    
    reviewer_large = results_large['reviewers'][('Jefferson County, Alabama', 'SNAP')]
    escalated_large = sum(s['applications_escalated'] for s in results_large['monthly_stats'])
    overflow_large = max(0, escalated_large - reviewer_large.applications_reviewed)
    
    print(f"  Reviewer capacity: {reviewer_large.monthly_capacity:.1f} units")
    print(f"  Escalations: {escalated_large}")
    print(f"  Reviewed: {reviewer_large.applications_reviewed}")
    print(f"  Overflow: {overflow_large} ({overflow_large/max(1,escalated_large)*100:.1f}% auto-approved)")
    
    print(f"\n→ Large county handles {overflow_small - overflow_large} more cases!")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Step 4: Reviewer Capacity Tracking")
    print("="*70)
    print("\nReviewers now:")
    print("  • Use complexity units (not simple count)")
    print("  • Capacity scales with county population")
    print("  • Check capacity before reviewing")
    print("  • Return CAPACITY_EXCEEDED if overloaded")
    print("\nResult: Realistic reviewer bottlenecks!")
    
    demo_reviewer_capacity()
    demo_small_vs_large_reviewer()
    
    print("\n" + "="*70)
    print("Step 4 Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  ✓ Reviewers use complexity-based capacity")
    print("  ✓ Small counties: ~5-6 units/month")
    print("  ✓ Large counties: ~250-270 units/month")
    print("  ✓ Complex cases consume more capacity")
    print("  ✓ Overflow cases auto-approved (realistic)")
    print("\nNext: Step 5 - Integration & Calibration")


if __name__ == "__main__":
    main()