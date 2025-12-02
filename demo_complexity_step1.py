"""
Demo: Application Complexity Scores (Step 1)

Shows how complexity is calculated for different applications.
Run with: python demo_complexity.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np

from src.core.seeker import Seeker


def demo_program_complexity():
    """Show how complexity varies by program."""
    print("=" * 70)
    print("COMPLEXITY BY PROGRAM")
    print("=" * 70)
    
    seeker = Seeker(1, 'White', 20000, county='TEST', has_children=False, has_disability=False)
    
    print("\nSame seeker applying to different programs:\n")
    print(f"  {'Program':<6} | {'Complexity':>10} | {'Interpretation'}")
    print(f"  {'-'*6}-+-{'-'*10}-+-{'-'*30}")
    
    for program in ['SNAP', 'TANF', 'SSI']:
        app = seeker.create_application(program, month=1, application_id=1)
        if app:
            print(f"  {program:<6} | {app.complexity:>10.2f} | ", end='')
            if app.complexity < 0.4:
                print("Simple")
            elif app.complexity < 0.7:
                print("Medium complexity")
            else:
                print("Complex")


def demo_disability_impact():
    """Show how disability affects complexity."""
    print("\n" + "=" * 70)
    print("DISABILITY IMPACT ON COMPLEXITY")
    print("=" * 70)
    
    no_disability = Seeker(1, 'Black', 15000, county='TEST', has_disability=False)
    has_disability = Seeker(2, 'Black', 15000, county='TEST', has_disability=True)
    
    print("\nSame program (SNAP), different disability status:\n")
    
    app1 = no_disability.create_application('SNAP', month=1, application_id=1)
    app2 = has_disability.create_application('SNAP', month=1, application_id=2)
    
    print(f"  No disability:  {app1.complexity:.2f}")
    print(f"  Has disability: {app2.complexity:.2f}")
    print(f"  Difference:     +{app2.complexity - app1.complexity:.2f} (disability adds verification)")


def demo_children_impact():
    """Show how children affect complexity."""
    print("\n" + "=" * 70)
    print("CHILDREN IMPACT ON COMPLEXITY")
    print("=" * 70)
    
    print("\nTANF applications with different numbers of children:\n")
    print(f"  {'Children':>8} | {'Complexity':>10} | {'Increase from 0'}")
    print(f"  {'-'*8}-+-{'-'*10}-+-{'-'*16}")
    
    for num_children in [0, 1, 2, 3, 4]:
        cps_data = {'household_size': num_children + 1, 'num_children': num_children}
        seeker = Seeker(
            num_children + 1, 
            'Hispanic', 
            12000, 
            county='TEST',
            has_children=(num_children > 0),
            cps_data=cps_data
        )
        
        app = seeker.create_application('TANF', month=1, application_id=num_children)
        if app:
            if num_children == 0:
                base_complexity = app.complexity
                print(f"  {num_children:>8} | {app.complexity:>10.2f} | (baseline)")
            else:
                increase = app.complexity - base_complexity
                print(f"  {num_children:>8} | {app.complexity:>10.2f} | +{increase:.2f}")


def demo_new_vs_recert():
    """Show new application vs recertification complexity."""
    print("\n" + "=" * 70)
    print("NEW vs RECERTIFICATION COMPLEXITY")
    print("=" * 70)
    
    seeker = Seeker(1, 'White', 18000, county='TEST', has_children=True)
    
    # New application
    new_app = seeker.create_application('SNAP', month=1, application_id=1)
    
    # Enroll (simulate approval)
    seeker.enroll_in_program('SNAP', month=1)
    
    # Recertification (6 months later)
    recert_app = seeker.create_application('SNAP', month=7, application_id=2)
    
    print("\nSame seeker, same program:\n")
    print(f"  New application:     {new_app.complexity:.2f}")
    print(f"  Recertification:     {recert_app.complexity:.2f}")
    print(f"  Reduction:          -{new_app.complexity - recert_app.complexity:.2f}")
    print(f"\n  → Recertification is simpler (already in system)")


def demo_complexity_distribution():
    """Show distribution of complexity across realistic population."""
    print("\n" + "=" * 70)
    print("COMPLEXITY DISTRIBUTION (Realistic Population)")
    print("=" * 70)
    
    # Create diverse seekers with CPS-like data
    seekers = []
    
    # Simple case
    seekers.append(Seeker(1, 'White', 25000, county='TEST'))
    
    # Medium case
    cps_medium = {'household_size': 3, 'num_children': 1, 'AGE': 32}
    seekers.append(Seeker(2, 'Black', 15000, county='TEST', has_children=True, cps_data=cps_medium))
    
    # Complex case
    cps_complex = {'household_size': 5, 'num_children': 3, 'AGE': 58}
    seekers.append(Seeker(3, 'Hispanic', 10000, county='TEST', has_children=True, 
                          has_disability=True, cps_data=cps_complex))
    
    print("\nApplications across different seekers and programs:\n")
    print(f"  {'Seeker':>6} | {'Program':>6} | {'Complexity':>10} | {'Category'}")
    print(f"  {'-'*6}-+-{'-'*6}-+-{'-'*10}-+-{'-'*20}")
    
    all_complexities = []
    for i, seeker in enumerate(seekers, 1):
        for program in ['SNAP', 'TANF', 'SSI']:
            app = seeker.create_application(program, month=1, application_id=i*10+ord(program[0]))
            if app:
                all_complexities.append(app.complexity)
                category = 'Simple' if app.complexity < 0.5 else 'Medium' if app.complexity < 0.8 else 'Complex'
                print(f"  {i:>6} | {program:>6} | {app.complexity:>10.2f} | {category}")
    
    print(f"\nComplexity distribution:")
    print(f"  Min: {min(all_complexities):.2f}")
    print(f"  Mean: {np.mean(all_complexities):.2f}")
    print(f"  Max: {max(all_complexities):.2f}")
    print(f"  Range: {max(all_complexities) - min(all_complexities):.2f}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Step 1: Complexity Calculation Demo")
    print("="*70)
    print("\nComplexity score = How difficult to process (0.0-1.0)")
    print("\nFactors:")
    print("  • Program: SSI > TANF > SNAP")
    print("  • Disability: +0.20 (medical verification)")
    print("  • Children: +0.03 per child")
    print("  • Household size: +0.05 per person")
    print("  • New application: +0.15 (vs recertification)")
    print("  • Age 65+: +0.10")
    
    demo_program_complexity()
    demo_disability_impact()
    demo_children_impact()
    demo_new_vs_recert()
    demo_complexity_distribution()
    
    print("\n" + "="*70)
    print("Step 1 Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  ✓ Complexity calculated for every application")
    print("  ✓ Ranges from 0.30 (simple SNAP) to 1.0 (complex SSI)")
    print("  ✓ Accounts for disability, children, household size")
    print("  ✓ New applications more complex than recerts")
    print("\nNext: Run pytest tests/test_complexity.py -v")


if __name__ == "__main__":
    main()