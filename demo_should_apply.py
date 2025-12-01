"""
Demo: Ultra-Simple Application Logic

Deterministic eligibility checks - no probabilities!
Run with: python demo_should_apply.py
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, 'src')

from core.seeker import Seeker


def demo_seeker_creation():
    """Show how to create seekers with the new simple interface."""
    print("=" * 70)
    print("CREATING SEEKERS")
    print("=" * 70)
    
    print("\nNow you specify everything explicitly:")
    print("\nseeker = Seeker(")
    print("    seeker_id=1,")
    print("    race='Black',")
    print("    income=25000,           # Annual income")
    print("    has_children=True,")
    print("    has_disability=False")
    print(")")
    
    seeker = Seeker(1, 'Black', 25000, has_children=True, has_disability=False)
    
    print(f"\nCreated: {seeker}")
    print(f"\nFraud propensity: {seeker.fraud_propensity:.2f} (0-2 scale)")
    print(f"Lying magnitude: {seeker.lying_magnitude:.1f}% (if fraudulent)")


def demo_eligibility_rules():
    """Show the simple eligibility rules."""
    print("\n" + "=" * 70)
    print("ELIGIBILITY RULES")
    print("=" * 70)
    print("\nSNAP (Food Assistance):")
    print("  ✓ Income < $2,500/month")
    
    print("\nTANF (Cash for Families):")
    print("  ✓ Income < $1,000/month")
    print("  ✓ Has children")
    
    print("\nSSI (Disability Benefits):")
    print("  ✓ Income < $1,913/month")
    print("  ✓ Has disability")


def demo_snap_examples():
    """Show SNAP eligibility examples."""
    print("\n" + "=" * 70)
    print("SNAP EXAMPLES")
    print("=" * 70)
    
    examples = [
        (18000, "Eligible"),    # $1,500/month
        (24000, "Eligible"),    # $2,000/month
        (30000, "NOT eligible"), # $2,500/month (at threshold)
        (50000, "NOT eligible"), # $4,167/month
    ]
    
    for income, expected in examples:
        seeker = Seeker(1, 'White', income)
        monthly = income / 12
        result = seeker.should_apply('SNAP', month=1)
        status = "✓ Applies" if result else "✗ Doesn't apply"
        
        print(f"\n  Income: ${income:>6,}/yr (${monthly:>6,.0f}/mo)")
        print(f"  Expected: {expected}")
        print(f"  Result: {status}")


def demo_multiple_programs():
    """Show one seeker's eligibility for multiple programs."""
    print("\n" + "=" * 70)
    print("MULTIPLE PROGRAMS - ONE SEEKER")
    print("=" * 70)
    
    seeker = Seeker(1, 'Black', 10000, has_children=True, has_disability=True)
    
    print(f"\nSeeker Profile:")
    print(f"  Income: ${seeker.income:,}/yr (${seeker.get_monthly_income():,.0f}/mo)")
    print(f"  Children: {seeker.has_children}")
    print(f"  Disability: {seeker.has_disability}")
    print(f"  Fraud propensity: {seeker.fraud_propensity:.2f}")
    print(f"  Lying magnitude: {seeker.lying_magnitude:.1f}%")
    
    print(f"\nProgram Eligibility:")
    programs = [
        ('SNAP', 'Income < $2,500/mo'),
        ('TANF', 'Income < $1,000/mo + children'),
        ('SSI', 'Income < $1,913/mo + disability')
    ]
    
    for program, rule in programs:
        result = seeker.should_apply(program, month=1)
        status = "✓ ELIGIBLE" if result else "✗ Not eligible"
        print(f"  {program:4s}: {status:15s} ({rule})")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Ultra-Simple Application Logic Demo")
    print("="*70)
    print("\nSimplified Seeker:")
    print("  • No automatic income generation")
    print("  • You specify: income, children, disability")
    print("  • Random: fraud_propensity (0-2) and lying_magnitude (0-100%)")
    
    demo_seeker_creation()
    demo_eligibility_rules()
    demo_snap_examples()
    demo_multiple_programs()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Changes:")
    print("  • Seeker creation is explicit (no hidden generation)")
    print("  • Added fraud_propensity (0-2)")
    print("  • Added lying_magnitude (0-100%)")
    print("  • Deterministic eligibility checks")
    print("\nNext: Run pytest tests/test_behavior.py -v")


if __name__ == "__main__":
    main()