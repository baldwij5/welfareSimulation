"""
Demo: Honest Errors vs Fraud

Shows the difference between:
- Honest applications (report truth)
- Honest errors (mistakes)
- Fraud (intentional lies)

Run with: python demo_errors.py
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, 'src')

from core.seeker import Seeker


def demo_three_types():
    """Show all three application types."""
    print("=" * 70)
    print("THREE TYPES OF APPLICATIONS")
    print("=" * 70)
    
    print("\n1. HONEST APPLICATION (No fraud, no error)")
    honest = Seeker(1, 'White', 20000, has_children=True, random_state=np.random.RandomState(42))
    honest.fraud_propensity = 0.0
    honest.error_propensity = 0.0
    
    app = honest.create_application('SNAP', month=1, application_id=1)
    print(f"   True income: ${app.true_income:,}")
    print(f"   Reported: ${app.reported_income:,}")
    print(f"   Discrepancy: ${app.get_income_discrepancy():,}")
    print(f"   Is fraud: {app.is_fraud}, Is error: {app.is_error}")
    
    print("\n2. HONEST ERROR (Mistake, not intentional)")
    error_seeker = Seeker(2, 'Black', 20000, has_children=True, random_state=np.random.RandomState(99))
    error_seeker.fraud_propensity = 0.0  # No fraud
    error_seeker.error_propensity = 2.0  # Force error
    error_seeker.error_magnitude = 15.0  # 15% error
    
    # Find an error application
    error_app = None
    for month in range(100):
        app = error_seeker.create_application('SNAP', month=month, application_id=100+month)
        if app and app.is_error:
            error_app = app
            break
    
    if error_app:
        discrepancy_pct = abs(error_app.get_income_discrepancy()) / error_app.true_income * 100
        direction = "over" if error_app.reported_income > error_app.true_income else "under"
        print(f"   True income: ${error_app.true_income:,}")
        print(f"   Reported: ${error_app.reported_income:,}")
        print(f"   Discrepancy: ${abs(error_app.get_income_discrepancy()):,} ({direction}reported {discrepancy_pct:.1f}%)")
        print(f"   Is fraud: {error_app.is_fraud}, Is error: {error_app.is_error}")
    
    print("\n3. FRAUDULENT APPLICATION (Intentional lie)")
    fraud_seeker = Seeker(3, 'Hispanic', 20000, has_children=True, random_state=np.random.RandomState(88))
    fraud_seeker.fraud_propensity = 2.0  # Force fraud
    fraud_seeker.lying_magnitude = 60.0  # 60% underreport
    
    # Find a fraud application
    fraud_app = None
    for month in range(100):
        app = fraud_seeker.create_application('SNAP', month=month, application_id=200+month)
        if app and app.is_fraud:
            fraud_app = app
            break
    
    if fraud_app:
        print(f"   True income: ${fraud_app.true_income:,}")
        print(f"   Reported: ${fraud_app.reported_income:,}")
        print(f"   Discrepancy: ${fraud_app.get_income_discrepancy():,} (underreported {fraud_app.get_income_discrepancy_pct():.1%})")
        print(f"   Is fraud: {fraud_app.is_fraud}, Is error: {fraud_app.is_error}")


def demo_error_direction():
    """Show that errors can go both directions."""
    print("\n" + "=" * 70)
    print("ERROR DIRECTION (Can Over- or Under-report)")
    print("=" * 70)
    
    seeker = Seeker(1, 'White', 20000, has_children=True, random_state=np.random.RandomState(42))
    seeker.fraud_propensity = 0.0  # No fraud
    seeker.error_propensity = 2.0  # Force errors
    seeker.error_magnitude = 15.0  # 15% error
    
    print(f"\nSeeker: Income=${seeker.income:,}, Error propensity={seeker.error_propensity:.2f}")
    print(f"Errors over 20 applications:\n")
    
    overreports = 0
    underreports = 0
    honest = 0
    
    for month in range(20):
        app = seeker.create_application('SNAP', month=month, application_id=month)
        if app:
            if app.is_error:
                if app.reported_income > app.true_income:
                    overreports += 1
                    print(f"  Month {month+1:2d}: ERROR (overreported) - Reported ${app.reported_income:>8,.0f}")
                else:
                    underreports += 1
                    print(f"  Month {month+1:2d}: ERROR (underreported) - Reported ${app.reported_income:>8,.0f}")
            else:
                honest += 1
                print(f"  Month {month+1:2d}: HONEST - Reported ${app.reported_income:>8,.0f}")
    
    print(f"\n  Summary: {honest} honest, {underreports} underreport errors, {overreports} overreport errors")


def demo_fraud_vs_error_magnitude():
    """Compare fraud lying magnitude vs error magnitude."""
    print("\n" + "=" * 70)
    print("FRAUD vs ERROR MAGNITUDE")
    print("=" * 70)
    
    print("\nFraud lying_magnitude: 0-100%")
    print("  → Large lies (can report almost $0)")
    print("  → Always underreports (to get benefits)")
    
    print("\nError error_magnitude: 0-20%")
    print("  → Small mistakes (off by 15-20%)")
    print("  → Can over- or under-report (honest confusion)")
    
    print("\nExamples with $20,000 true income:\n")
    
    # Fraud example
    print("FRAUD (lying_magnitude = 80%):")
    print(f"  Reported: ${20000 * 0.2:,.0f} (underreported 80%)")
    
    # Error examples
    print("\nERROR (error_magnitude = 15%):")
    print(f"  Underreport: ${20000 * 0.85:,.0f} (off by 15%)")
    print(f"  Overreport: ${20000 * 1.15:,.0f} (off by 15%)")


def demo_application_breakdown():
    """Show breakdown of honest/error/fraud in a population."""
    print("\n" + "=" * 70)
    print("POPULATION APPLICATION BREAKDOWN")
    print("=" * 70)
    
    # Create 100 seekers
    seekers = [Seeker(i, 'White', 20000, has_children=True, random_state=np.random.RandomState(i))
               for i in range(100)]
    
    # Generate applications for month 1
    applications = []
    for i, seeker in enumerate(seekers):
        app = seeker.create_application('SNAP', month=1, application_id=i)
        if app:
            applications.append(app)
    
    # Count types
    honest = sum(1 for app in applications if not app.is_fraud and not app.is_error)
    errors = sum(1 for app in applications if app.is_error)
    fraud = sum(1 for app in applications if app.is_fraud)
    
    print(f"\n100 seekers applying for SNAP in month 1:")
    print(f"  Total applications: {len(applications)}")
    print(f"\n  Honest: {honest:3d} ({honest/len(applications)*100:5.1f}%)")
    print(f"  Errors: {errors:3d} ({errors/len(applications)*100:5.1f}%)")
    print(f"  Fraud:  {fraud:3d} ({fraud/len(applications)*100:5.1f}%)")
    
    # Show some examples
    print(f"\nExample applications:")
    for app in applications[:5]:
        app_type = "FRAUD" if app.is_fraud else "ERROR" if app.is_error else "HONEST"
        print(f"  {app_type:7s}: True=${app.true_income:>7,.0f}, Reported=${app.reported_income:>7,.0f}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Honest Errors vs Fraud Demo")
    print("="*70)
    print("\nThree types of applications:")
    print("  1. HONEST - Report truth (fraud_propensity=0, error_propensity=0)")
    print("  2. ERROR - Honest mistake (error_propensity>1, error_magnitude=0-20%)")
    print("  3. FRAUD - Intentional lie (fraud_propensity>1, lying_magnitude=0-100%)")
    print("\nKey difference:")
    print("  • Errors: Small (0-20%), can go either direction")
    print("  • Fraud: Large (0-100%), always underreports")
    
    demo_three_types()
    demo_error_direction()
    demo_fraud_vs_error_magnitude()
    demo_application_breakdown()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  • Errors are honest mistakes (small, bidirectional)")
    print("  • Fraud is intentional (large, always underreports)")
    print("  • Application can't be both fraud AND error")
    print("  • Typical: 70-80% honest, 10-15% error, 5-10% fraud")
    print("\nNext: Run pytest tests/test_behavior.py::TestErrorDecision -v")


if __name__ == "__main__":
    main()