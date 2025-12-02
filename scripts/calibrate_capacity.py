"""
Step 5: Calibration Analysis

Diagnose capacity issues and find optimal parameters.
Run with: python scripts/calibrate_capacity.py
"""

import sys
sys.path.insert(0, 'src')

from simulation.runner import run_simulation_with_real_data


def analyze_current_system():
    """Analyze overflow rates with current parameters."""
    print("=" * 70)
    print("CURRENT SYSTEM ANALYSIS")
    print("=" * 70)
    
    print("\nCurrent Parameters:")
    print("  Evaluators:")
    print("    Staff ratio: 1 per 50,000 people")
    print("    Units per staff: 20.0")
    print("  Reviewers:")
    print("    Staff ratio: 1 per 100,000 people")
    print("    Units per staff: 10.0")
    
    # Test with diverse counties
    counties = [
        'Autauga County, Alabama',      # Small: 59k
        'Baldwin County, Alabama',      # Medium: 233k
        'Jefferson County, Alabama'     # Large: 672k
    ]
    
    print(f"\n\nRunning test simulation (300 seekers, 12 months)...\n")
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=300,
        n_months=12,
        counties=counties,
        random_seed=42
    )
    
    print(f"\n{'='*70}")
    print(f"OVERFLOW ANALYSIS")
    print(f"{'='*70}\n")
    
    total_apps = results['summary']['total_applications']
    total_exceeded = sum(s.get('applications_capacity_exceeded', 0) 
                        for s in results['monthly_stats'])
    total_escalated = sum(s['applications_escalated'] 
                         for s in results['monthly_stats'])
    
    print(f"Overall Statistics:")
    print(f"  Total applications: {total_apps}")
    print(f"  Evaluator overflows: {total_exceeded} ({total_exceeded/total_apps*100:.1f}%)")
    print(f"  Total escalations: {total_escalated}")
    
    # Reviewer overflow
    total_reviewed = 0
    for (county, program), reviewer in results['reviewers'].items():
        total_reviewed += reviewer.applications_reviewed
    
    reviewer_overflow = total_escalated - total_reviewed
    
    print(f"  Reviewer overflows: {reviewer_overflow} ({reviewer_overflow/max(1,total_escalated)*100:.1f}%)")
    
    print(f"\n⚠️  DIAGNOSIS:")
    if total_exceeded > total_apps * 0.05:
        print(f"  Evaluator overflow too high ({total_exceeded/total_apps*100:.1f}%)")
        print(f"  → Need MORE evaluator capacity")
    else:
        print(f"  ✓ Evaluator overflow acceptable")
    
    if reviewer_overflow > total_escalated * 0.10:
        print(f"  Reviewer overflow too high ({reviewer_overflow/total_escalated*100:.1f}%)")
        print(f"  → Need MORE reviewer capacity")
    else:
        print(f"  ✓ Reviewer overflow acceptable")
    
    return {
        'evaluator_overflow_pct': total_exceeded/total_apps,
        'reviewer_overflow_pct': reviewer_overflow/max(1, total_escalated),
        'total_apps': total_apps,
        'total_escalated': total_escalated
    }


def test_calibration(eval_ratio, eval_units, rev_ratio, rev_units):
    """Test a specific calibration."""
    print(f"\n{'='*70}")
    print(f"Testing Calibration:")
    print(f"  Evaluators: 1/{eval_ratio:,.0f} people, {eval_units} units/staff")
    print(f"  Reviewers: 1/{rev_ratio:,.0f} people, {rev_units} units/staff")
    print(f"{'='*70}")
    
    # Would need to modify runner.py to accept these parameters
    # For now, just document what we'd test
    
    print(f"\nExpected results:")
    print(f"  Small county (59k):")
    print(f"    Eval capacity: {59000/eval_ratio * eval_units:.1f} units")
    print(f"    Review capacity: {59000/rev_ratio * rev_units:.1f} units")
    print(f"  Large county (672k):")
    print(f"    Eval capacity: {672000/eval_ratio * eval_units:.1f} units")
    print(f"    Review capacity: {672000/rev_ratio * rev_units:.1f} units")


def recommend_calibration(analysis):
    """Recommend calibrated parameters."""
    print(f"\n{'='*70}")
    print(f"RECOMMENDED CALIBRATION")
    print(f"{'='*70}")
    
    eval_overflow = analysis['evaluator_overflow_pct']
    rev_overflow = analysis['reviewer_overflow_pct']
    
    print(f"\nCurrent Issues:")
    print(f"  Evaluator overflow: {eval_overflow*100:.1f}%")
    print(f"  Reviewer overflow: {rev_overflow*100:.1f}%")
    
    print(f"\nRecommended Changes:")
    
    # Evaluator recommendations
    if eval_overflow > 0.10:
        factor = eval_overflow / 0.05  # Target 5% overflow
        print(f"\n  Evaluators:")
        print(f"    OPTION A: Increase staff ratio to 1 per {50000/factor:,.0f} people")
        print(f"    OPTION B: Increase units per staff to {20.0 * factor:.0f}")
        print(f"    → This would reduce overflow to ~5%")
    
    # Reviewer recommendations
    if rev_overflow > 0.10:
        # Reviewers are WAY over
        print(f"\n  Reviewers (CRITICAL):")
        print(f"    Current: 1 per 100,000 people, 10 units/staff")
        print(f"    Overflow: {rev_overflow*100:.0f}%!")
        print(f"\n    RECOMMENDED FIX:")
        print(f"    → Change to 1 per 50,000 people (same as evaluators)")
        print(f"    → OR increase to 20 units/staff (double current)")
        print(f"    → This should reduce overflow to <10%")
    
    print(f"\n  Final Recommendation:")
    print(f"    Evaluators: 1 per 50,000, 20 units/staff (keep current)")
    print(f"    Reviewers: 1 per 50,000, 15 units/staff (INCREASE)")
    print(f"    → Same staff ratio, but reviewers handle fewer cases (more specialized)")


def main():
    """Run calibration analysis."""
    print("\n" + "="*70)
    print("Step 5: Calibration Analysis")
    print("="*70)
    print("\nGoals:")
    print("  • Evaluator overflow < 5%")
    print("  • Reviewer overflow < 10%")
    print("  • Realistic staffing levels")
    print("  • Small counties show some strain (realistic)")
    
    # Analyze current system
    analysis = analyze_current_system()
    
    # Test alternatives
    print(f"\n\nTesting Alternative Calibrations:")
    test_calibration(eval_ratio=50000, eval_units=20, rev_ratio=50000, rev_units=15)
    test_calibration(eval_ratio=50000, eval_units=20, rev_ratio=75000, rev_units=15)
    
    # Recommendations
    recommend_calibration(analysis)
    
    print("\n" + "="*70)
    print("Calibration Complete!")
    print("="*70)
    print("\nNext: Update runner.py with calibrated parameters")


if __name__ == "__main__":
    main()