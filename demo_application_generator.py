"""
Demo: Application Generation

Shows how create_application() combines eligibility + fraud decisions.
Run with: python demo_application_generation.py
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, 'src')

from core.seeker import Seeker


def demo_honest_application():
    """Show honest application generation."""
    print("=" * 70)
    print("HONEST APPLICATION")
    print("=" * 70)
    
    # Create honest seeker (low fraud propensity)
    seeker = Seeker(1, 'Black', 20000, has_children=True, random_state=np.random.RandomState(42))
    seeker.fraud_propensity = 0.0  # Force honest
    
    print(f"\nSeeker Profile:")
    print(f"  Income: ${seeker.income:,}")
    print(f"  Children: {seeker.has_children}")
    print(f"  Fraud propensity: {seeker.fraud_propensity:.2f} (honest)")
    print(f"  Lying magnitude: {seeker.lying_magnitude:.1f}%")
    
    # Create application
    app = seeker.create_application('SNAP', month=1, application_id=1)
    
    if app:
        print(f"\nApplication Created:")
        print(f"  Program: {app.program}")
        print(f"  Month: {app.month}")
        print(f"  Is fraud: {app.is_fraud}")
        print(f"  True income: ${app.true_income:,.0f}")
        print(f"  Reported income: ${app.reported_income:,.0f}")
        print(f"  Discrepancy: ${app.get_income_discrepancy():,.0f}")
        print(f"\n  → Honest application (reports truth)")


def demo_fraudulent_application():
    """Show fraudulent application generation."""
    print("\n" + "=" * 70)
    print("FRAUDULENT APPLICATION")
    print("=" * 70)
    
    # Create fraudulent seeker (high fraud propensity)
    seeker = Seeker(2, 'White', 40000, has_children=True, random_state=np.random.RandomState(99))
    seeker.fraud_propensity = 2.0  # Force fraud
    
    print(f"\nSeeker Profile:")
    print(f"  Income: ${seeker.income:,}")
    print(f"  Children: {seeker.has_children}")
    print(f"  Fraud propensity: {seeker.fraud_propensity:.2f} (high risk)")
    print(f"  Lying magnitude: {seeker.lying_magnitude:.1f}%")
    
    # Try creating applications until we get fraud
    fraud_app = None
    for month in range(20):
        app = seeker.create_application('SNAP', month=month, application_id=100+month)
        if app and app.is_fraud:
            fraud_app = app
            break
    
    if fraud_app:
        print(f"\nFraudulent Application (Month {fraud_app.month}):")
        print(f"  Program: {fraud_app.program}")
        print(f"  Is fraud: {fraud_app.is_fraud}")
        print(f"  True income: ${fraud_app.true_income:,.0f}")
        print(f"  Reported income: ${fraud_app.reported_income:,.0f}")
        print(f"  Discrepancy: ${fraud_app.get_income_discrepancy():,.0f}")
        print(f"  Underreporting: {fraud_app.get_income_discrepancy_pct():.1%}")
        print(f"\n  → Fraudulent application (underreported income)")


def demo_ineligible_seeker():
    """Show that ineligible seekers don't create applications."""
    print("\n" + "=" * 70)
    print("INELIGIBLE SEEKER")
    print("=" * 70)
    
    # High-income seeker (not eligible)
    seeker = Seeker(3, 'White', 100000, has_children=True)
    
    print(f"\nSeeker Profile:")
    print(f"  Income: ${seeker.income:,} (${seeker.get_monthly_income():,.0f}/month)")
    print(f"  Children: {seeker.has_children}")
    
    # Try to create application
    app = seeker.create_application('SNAP', month=1, application_id=200)
    
    print(f"\nApplication Result:")
    if app is None:
        print(f"  → None (seeker not eligible for SNAP)")
        print(f"  → Income ${seeker.get_monthly_income():,.0f}/mo exceeds $2,500 threshold")
    else:
        print(f"  → Application created (unexpected!)")


def demo_multiple_programs():
    """Show creating applications for multiple programs."""
    print("\n" + "=" * 70)
    print("MULTIPLE PROGRAMS - ONE SEEKER")
    print("=" * 70)
    
    # Seeker eligible for all programs
    seeker = Seeker(4, 'Black', 10000, has_children=True, has_disability=True,
                   random_state=np.random.RandomState(42))
    
    print(f"\nSeeker Profile:")
    print(f"  Income: ${seeker.income:,} (${seeker.get_monthly_income():,.0f}/month)")
    print(f"  Children: {seeker.has_children}")
    print(f"  Disability: {seeker.has_disability}")
    print(f"  Fraud propensity: {seeker.fraud_propensity:.2f}")
    
    print(f"\nCreating applications for all programs:")
    
    app_id = 300
    for program in ['SNAP', 'TANF', 'SSI']:
        app = seeker.create_application(program, month=1, application_id=app_id)
        app_id += 1
        
        if app:
            fraud_status = "FRAUD" if app.is_fraud else "HONEST"
            print(f"\n  {program}:")
            print(f"    Status: {fraud_status}")
            print(f"    True income: ${app.true_income:,.0f}")
            print(f"    Reported: ${app.reported_income:,.0f}")


def demo_application_over_time():
    """Show applications over multiple months."""
    print("\n" + "=" * 70)
    print("APPLICATIONS OVER TIME")
    print("=" * 70)
    
    seeker = Seeker(5, 'Black', 20000, has_children=True, random_state=np.random.RandomState(42))
    
    print(f"\nSeeker: Income=${seeker.income:,}, Fraud propensity={seeker.fraud_propensity:.2f}")
    print(f"\nCreating SNAP applications over 12 months:\n")
    
    honest_count = 0
    fraud_count = 0
    
    for month in range(1, 13):
        app = seeker.create_application('SNAP', month=month, application_id=400+month)
        
        if app:
            status = "FRAUD" if app.is_fraud else "HONEST"
            symbol = "🚨" if app.is_fraud else "✓"
            
            if app.is_fraud:
                fraud_count += 1
                underreport = (app.true_income - app.reported_income) / app.true_income * 100
                print(f"  Month {month:2d}: {symbol} {status:7s} - Reported ${app.reported_income:>8,.0f} (underreporting {underreport:.0f}%)")
            else:
                honest_count += 1
                print(f"  Month {month:2d}: {symbol} {status:7s} - Reported ${app.reported_income:>8,.0f}")
    
    print(f"\n  Summary: {honest_count} honest, {fraud_count} fraudulent")
    print(f"  Total applications: {seeker.num_applications}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Application Generation Demo")
    print("="*70)
    print("\ncreate_application() combines:")
    print("  1. Eligibility check (should_apply)")
    print("  2. Fraud decision (will_commit_fraud)")
    print("  3. Income calculation (lying_magnitude if fraud)")
    print("  → Returns Application object (or None if ineligible)")
    
    demo_honest_application()
    demo_fraudulent_application()
    demo_ineligible_seeker()
    demo_multiple_programs()
    demo_application_over_time()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  • Ineligible seekers return None")
    print("  • Honest applications report true income")
    print("  • Fraudulent applications underreport by lying_magnitude")
    print("  • num_applications tracks total applications")
    print("  • Same seeker can create multiple applications over time")
    print("\nNext: Run pytest tests/test_behavior.py::TestApplicationGeneration -v")


if __name__ == "__main__":
    main()