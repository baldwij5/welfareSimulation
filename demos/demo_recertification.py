"""
Demo: Recertification Schedule

Shows how benefits expire and require renewal.
Run with: python demo_recertification.py
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, 'src')

from src.core.seeker import Seeker


def demo_recertification_schedules():
    """Show the different recertification schedules."""
    print("=" * 70)
    print("RECERTIFICATION SCHEDULES")
    print("=" * 70)
    
    print("\nProgram recertification periods:")
    print("  SNAP: Every 6 months")
    print("  TANF: Every 12 months")
    print("  SSI: Every 36 months")


def demo_snap_recertification():
    """Show SNAP recertification over time."""
    print("\n" + "=" * 70)
    print("SNAP RECERTIFICATION (6-month cycle)")
    print("=" * 70)
    
    seeker = Seeker(1, 'Black', 20000, has_children=True)
    
    print(f"\nSeeker enrolled in SNAP at month 0")
    seeker.enroll_in_program('SNAP', month=0)
    
    print("\nApplication pattern over 18 months:")
    print(f"  {'Month':>5} | {'Enrolled?':^10} | {'Should Apply?':^15} | {'Status'}")
    print(f"  {'-'*5}-+-{'-'*10}-+-{'-'*15}-+-{'-'*30}")
    
    for month in range(19):
        enrolled = seeker.is_enrolled('SNAP')
        should_apply = seeker.should_apply('SNAP', month)
        
        # Simulate approval if they apply
        if should_apply:
            seeker.enroll_in_program('SNAP', month)
            status = "→ Applied & approved (enrolled)"
        else:
            status = "  (Currently receiving benefits)"
        
        enrolled_str = "Yes" if enrolled else "No"
        apply_str = "Yes" if should_apply else "No"
        
        print(f"  {month:>5} | {enrolled_str:^10} | {apply_str:^15} | {status}")


def demo_multiple_programs():
    """Show multiple programs with different schedules."""
    print("\n" + "=" * 70)
    print("MULTIPLE PROGRAMS - DIFFERENT SCHEDULES")
    print("=" * 70)
    
    seeker = Seeker(1, 'White', 10000, has_children=True, has_disability=True)
    
    # Enroll in all at month 0
    seeker.enroll_in_program('SNAP', month=0)
    seeker.enroll_in_program('TANF', month=0)
    seeker.enroll_in_program('SSI', month=0)
    
    print("\nEnrolled in all programs at month 0")
    print("\nRecertification pattern over 36 months:")
    print(f"  {'Month':>5} | {'SNAP (6mo)':^12} | {'TANF (12mo)':^13} | {'SSI (36mo)':^12}")
    print(f"  {'-'*5}-+-{'-'*12}-+-{'-'*13}-+-{'-'*12}")
    
    for month in [0, 6, 12, 18, 24, 30, 36]:
        snap = "RECERT" if seeker.should_apply('SNAP', month) else "Enrolled"
        tanf = "RECERT" if seeker.should_apply('TANF', month) else "Enrolled"
        ssi = "RECERT" if seeker.should_apply('SSI', month) else "Enrolled"
        
        # Re-enroll if they applied
        if seeker.should_apply('SNAP', month):
            seeker.enroll_in_program('SNAP', month)
        if seeker.should_apply('TANF', month):
            seeker.enroll_in_program('TANF', month)
        if seeker.should_apply('SSI', month):
            seeker.enroll_in_program('SSI', month)
        
        print(f"  {month:>5} | {snap:^12} | {tanf:^13} | {ssi:^12}")


def demo_benefit_loss():
    """Show what happens if seeker doesn't recertify."""
    print("\n" + "=" * 70)
    print("BENEFIT LOSS (Failed to Recertify)")
    print("=" * 70)
    
    seeker = Seeker(1, 'Hispanic', 25000, has_children=True)
    
    print("\nScenario: Seeker approved for SNAP at month 0, but doesn't recertify")
    
    # Enroll at month 0
    seeker.enroll_in_program('SNAP', month=0)
    print(f"\nMonth 0: Enrolled in SNAP")
    
    # Check months 1-5 (should not apply, still enrolled)
    print(f"Months 1-5: Still receiving benefits (no action needed)")
    
    # Month 6: Recertification due
    print(f"\nMonth 6: Recertification due!")
    should_apply = seeker.should_apply('SNAP', month=6)
    print(f"  Should apply? {should_apply}")
    print(f"  Enrolled? {seeker.is_enrolled('SNAP')} (expired during check)")
    
    # If seeker doesn't apply (e.g., becomes ineligible), they lose benefits
    print(f"\nMonth 7: Not enrolled anymore (lost benefits)")
    print(f"  Enrolled? {seeker.is_enrolled('SNAP')}")


def demo_continuous_enrollment():
    """Show seeker maintaining enrollment through recertifications."""
    print("\n" + "=" * 70)
    print("CONTINUOUS ENROLLMENT (Successful Recertifications)")
    print("=" * 70)
    
    seeker = Seeker(1, 'Black', 15000, has_children=True)
    
    print("\nSeeker maintains SNAP enrollment for 18 months:")
    
    applications = []
    
    for month in range(19):
        if seeker.should_apply('SNAP', month):
            applications.append(month)
            # Simulate approval
            seeker.enroll_in_program('SNAP', month)
            print(f"\nMonth {month}: RECERTIFICATION")
            print(f"  → Applied and approved")
            print(f"  → Benefits continue")
        else:
            if month % 6 == 0:  # Show status every 6 months
                print(f"\nMonth {month}: Receiving benefits")
    
    print(f"\n\nSummary:")
    print(f"  Applied/recertified at months: {applications}")
    print(f"  Total applications: {len(applications)}")
    print(f"  Maintained enrollment for 18 months ✓")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Recertification Schedule Demo")
    print("="*70)
    print("\nBenefits expire and require renewal:")
    print("  • SNAP: Every 6 months")
    print("  • TANF: Every 12 months")
    print("  • SSI: Every 36 months")
    print("\nSeeker must reapply or lose benefits!")
    
    demo_recertification_schedules()
    demo_snap_recertification()
    demo_multiple_programs()
    demo_benefit_loss()
    demo_continuous_enrollment()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  • Benefits expire after recertification period")
    print("  • Seeker must reapply to maintain benefits")
    print("  • Different programs have different schedules")
    print("  • Can be enrolled in multiple programs simultaneously")
    print("  • Failure to recertify = lose benefits")
    print("\nNext: Run pytest tests/test_behavior.py::TestRecertification -v")


if __name__ == "__main__":
    main()