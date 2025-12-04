"""
Demo: Complete Simulation

Shows the full simulation running over time.
Run with: python demo_simulation.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from simulation.runner import run_simulation


def demo_small_simulation():
    """Run a small simulation and show results."""
    print("=" * 70)
    print("SMALL SIMULATION: 20 Seekers, 6 Months")
    print("=" * 70)
    
    results = run_simulation(n_seekers=20, n_months=6, random_seed=42)
    
    print("\nOverall Summary:")
    print(f"  Seekers: {results['summary']['total_seekers']}")
    print(f"  Months: {results['summary']['total_months']}")
    print(f"  Applications: {results['summary']['total_applications']}")
    print(f"  Approved: {results['summary']['total_approvals']}")
    print(f"  Denied: {results['summary']['total_denials']}")
    print(f"  Investigated: {results['summary']['total_investigations']}")
    print(f"  Approval rate: {results['summary']['approval_rate']:.1%}")
    
    print("\nMonthly Breakdown:")
    print(f"  {'Month':>5} | {'Apps':>4} | {'Approved':>8} | {'Denied':>6} | {'Fraud':>5} | {'Errors':>6}")
    print(f"  {'-'*5}-+-{'-'*4}-+-{'-'*8}-+-{'-'*6}-+-{'-'*5}-+-{'-'*6}")
    
    for stats in results['monthly_stats']:
        print(f"  {stats['month']:>5} | {stats['applications_submitted']:>4} | "
              f"{stats['applications_approved']:>8} | {stats['applications_denied']:>6} | "
              f"{stats['fraud_attempted']:>5} | {stats['errors_made']:>6}")


def demo_medium_simulation():
    """Run a medium simulation."""
    print("\n" + "=" * 70)
    print("MEDIUM SIMULATION: 100 Seekers, 12 Months")
    print("=" * 70)
    
    results = run_simulation(n_seekers=100, n_months=12, random_seed=42)
    
    print("\nOverall Summary:")
    print(f"  Total applications: {results['summary']['total_applications']}")
    print(f"  Approved: {results['summary']['total_approvals']} ({results['summary']['approval_rate']:.1%})")
    print(f"  Denied: {results['summary']['total_denials']}")
    print(f"  Investigated: {results['summary']['total_investigations']} ({results['summary']['investigation_rate']:.1%})")
    
    # Application type breakdown
    total_fraud = sum(s['fraud_attempted'] for s in results['monthly_stats'])
    total_errors = sum(s['errors_made'] for s in results['monthly_stats'])
    total_honest = sum(s['honest_applications'] for s in results['monthly_stats'])
    total_apps = results['summary']['total_applications']
    
    print("\nApplication Types:")
    print(f"  Honest: {total_honest} ({total_honest/total_apps*100:.1f}%)")
    print(f"  Errors: {total_errors} ({total_errors/total_apps*100:.1f}%)")
    print(f"  Fraud: {total_fraud} ({total_fraud/total_apps*100:.1f}%)")
    
    # Seeker participation
    seekers_who_applied = sum(1 for s in results['seekers'] if s.num_applications > 0)
    seekers_approved = sum(1 for s in results['seekers'] if s.num_approvals > 0)
    
    print("\nSeeker Participation:")
    print(f"  Applied at least once: {seekers_who_applied}/{results['summary']['total_seekers']} ({seekers_who_applied/results['summary']['total_seekers']*100:.1f}%)")
    print(f"  Approved at least once: {seekers_approved}/{results['summary']['total_seekers']} ({seekers_approved/results['summary']['total_seekers']*100:.1f}%)")


def demo_seeker_histories():
    """Show individual seeker histories."""
    print("\n" + "=" * 70)
    print("INDIVIDUAL SEEKER HISTORIES")
    print("=" * 70)
    
    results = run_simulation(n_seekers=50, n_months=12, random_seed=42)
    
    # Find interesting seekers
    most_active = max(results['seekers'], key=lambda s: s.num_applications)
    most_approved = max(results['seekers'], key=lambda s: s.num_approvals)
    
    print("\nMost Active Seeker:")
    print(f"  ID: {most_active.id}")
    print(f"  Race: {most_active.race}")
    print(f"  Income: ${most_active.income:,.0f}")
    print(f"  Applications: {most_active.num_applications}")
    print(f"  Approved: {most_active.num_approvals}")
    print(f"  Denied: {most_active.num_denials}")
    print(f"  Investigated: {most_active.num_investigations}")
    
    print("\nMost Successful Seeker:")
    print(f"  ID: {most_approved.id}")
    print(f"  Race: {most_approved.race}")
    print(f"  Income: ${most_approved.income:,.0f}")
    print(f"  Applications: {most_approved.num_applications}")
    print(f"  Approved: {most_approved.num_approvals}")
    print(f"  Success rate: {most_approved.num_approvals/max(1, most_approved.num_applications):.1%}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Complete Simulation Demo")
    print("="*70)
    print("\nThe simulation runs seekers over multiple months:")
    print("  1. Seekers create applications")
    print("  2. Evaluators process applications")
    print("  3. Reviewers handle escalations")
    print("  4. Track outcomes and statistics")
    
    demo_small_simulation()
    demo_medium_simulation()
    demo_seeker_histories()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nThe simulation is working!")
    print("  ✓ Population created")
    print("  ✓ Monthly loop running")
    print("  ✓ Applications processed")
    print("  ✓ Statistics tracked")
    print("\nNext: Run pytest tests/test_simulation.py -v")


if __name__ == "__main__":
    main()