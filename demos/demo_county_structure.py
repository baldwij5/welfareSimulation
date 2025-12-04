"""
Demo: County-Program Structure

Shows how evaluators are organized by county and program.
Run with: python demo_county_structure.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from simulation.runner import create_population, create_evaluators, create_reviewers, run_simulation


def demo_county_assignment():
    """Show how seekers are assigned to counties."""
    print("=" * 70)
    print("SEEKER COUNTY ASSIGNMENT")
    print("=" * 70)
    
    counties = ['Kings County, NY', 'Cook County, IL', 'Los Angeles County, CA']
    seekers = create_population(n_seekers=12, counties=counties, random_seed=42)
    
    print(f"\nCreated 12 seekers across 3 counties:")
    print(f"\n  {'ID':>3} | {'County':^25} | {'Race':^10} | {'Income':>10}")
    print(f"  {'-'*3}-+-{'-'*25}-+-{'-'*10}-+-{'-'*10}")
    
    for seeker in seekers:
        print(f"  {seeker.id:>3} | {seeker.county:^25} | {seeker.race:^10} | ${seeker.income:>9,.0f}")
    
    # Count by county
    print(f"\nSeeker distribution:")
    for county in counties:
        count = sum(1 for s in seekers if s.county == county)
        print(f"  {county}: {count} seekers")


def demo_evaluator_structure():
    """Show evaluator structure (one per county-program)."""
    print("\n" + "=" * 70)
    print("EVALUATOR STRUCTURE")
    print("=" * 70)
    
    counties = ['County_A', 'County_B']
    evaluators = create_evaluators(counties, random_seed=42)
    
    print(f"\nCreated {len(evaluators)} evaluators:")
    print(f"  (Each county × each program = 1 evaluator)")
    
    print(f"\n  {'County':^12} | {'Program':^6} | {'Evaluator ID':>12} | {'Strictness':>10}")
    print(f"  {'-'*12}-+-{'-'*6}-+-{'-'*12}-+-{'-'*10}")
    
    for (county, program), evaluator in sorted(evaluators.items()):
        print(f"  {county:^12} | {program:^6} | {evaluator.id:>12} | {evaluator.strictness:>10.2f}")
    
    print(f"\nTotal: {len(counties)} counties × 3 programs = {len(evaluators)} evaluators")


def demo_reviewer_structure():
    """Show reviewer structure (one per county-program)."""
    print("\n" + "=" * 70)
    print("REVIEWER STRUCTURE")
    print("=" * 70)
    
    counties = ['County_A', 'County_B', 'County_C']
    reviewers = create_reviewers(counties, random_seed=42)
    
    print(f"\nCreated {len(reviewers)} reviewers (1 per county-program):")
    
    print(f"\n  {'County':^12} | {'Program':^7} | {'Reviewer ID':>12} | {'Capacity':>8} | {'Accuracy':>8}")
    print(f"  {'-'*12}-+-{'-'*7}-+-{'-'*12}-+-{'-'*8}-+-{'-'*8}")
    
    for (county, program), reviewer in sorted(reviewers.items()):
        print(f"  {county:^12} | {program:^7} | {reviewer.id:>12} | {reviewer.capacity:>8} | {reviewer.accuracy:>7.1%}")


def demo_application_routing():
    """Show how applications are routed to correct evaluator."""
    print("\n" + "=" * 70)
    print("APPLICATION ROUTING")
    print("=" * 70)
    
    print("\nExample: Seeker in County_A applies for SNAP")
    print("  → Routed to County_A SNAP Evaluator")
    print("  → AND County_A SNAP Reviewer (if escalated)")
    print("  → NOT County_B team")
    print("  → NOT County_A TANF team")
    
    print("\nExample: Seeker in County_B applies for SSI")
    print("  → Routed to County_B SSI Evaluator")
    print("  → AND County_B SSI Reviewer (if escalated)")
    
    print("\nEach county-program has dedicated staff:")
    print("  → County_A SNAP: Evaluator + Reviewer")
    print("  → County_A TANF: Evaluator + Reviewer")
    print("  → County_A SSI: Evaluator + Reviewer")
    print("  (Total: 3 evaluators + 3 reviewers per county)")
    
    print("\n→ Each county-program team operates independently!")


def demo_full_simulation_with_counties():
    """Run simulation with multiple counties."""
    print("\n" + "=" * 70)
    print("FULL SIMULATION WITH 3 COUNTIES")
    print("=" * 70)
    
    counties = ['County_A', 'County_B', 'County_C']
    
    results = run_simulation(
        n_seekers=30,  # 10 per county
        n_months=12,
        counties=counties,
        random_seed=42
    )
    
    print(f"\nSimulation Summary:")
    print(f"  Counties: {len(results['counties'])}")
    print(f"  Evaluators: {len(results['evaluators'])} (3 counties × 3 programs)")
    print(f"  Reviewers: {len(results['reviewers'])} (1 per county)")
    print(f"  Seekers: {results['summary']['total_seekers']}")
    print(f"  Applications: {results['summary']['total_applications']}")
    
    # Breakdown by county
    print(f"\nSeeker distribution by county:")
    for county in counties:
        county_seekers = [s for s in results['seekers'] if s.county == county]
        county_apps = sum(s.num_applications for s in county_seekers)
        print(f"  {county}: {len(county_seekers)} seekers, {county_apps} applications")
    
    # Evaluator workload
    print(f"\nEvaluator workload:")
    for (county, program), evaluator in sorted(results['evaluators'].items()):
        print(f"  {county} {program}: {evaluator.applications_processed} applications processed")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("County-Program Structure Demo")
    print("="*70)
    print("\nKey concepts:")
    print("  • Each seeker belongs to ONE county")
    print("  • Each county has evaluators for SNAP, TANF, SSI (3 evaluators)")
    print("  • Each county has ONE reviewer (handles all programs)")
    print("  • Applications route to correct county-program evaluator")
    print("\nStructure: Counties operate independently")
    
    demo_county_assignment()
    demo_evaluator_structure()
    demo_reviewer_structure()
    demo_application_routing()
    demo_full_simulation_with_counties()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  • Seekers assigned to counties")
    print("  • 1 evaluator per county-program combination")
    print("  • 1 reviewer per county (all programs)")
    print("  • Applications routed correctly")
    print("  • Counties operate independently")
    print("\nNext: You can now test county-level differences!")


if __name__ == "__main__":
    main()