"""
Demo: Bureaucracy Navigation Points System

Shows how investigation works with points-based system.
Run with: python demo_bureaucracy_points.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np

from src.core.seeker import Seeker
from src.core.reviewer import Reviewer
from src.core.application import Application


def demo_point_generation():
    """Show how bureaucracy points are generated."""
    print("=" * 70)
    print("BUREAUCRACY NAVIGATION POINTS")
    print("=" * 70)
    
    print("\nPoints represent ability to navigate bureaucratic investigation:")
    print("  • Provide documentation")
    print("  • Respond to verification")
    print("  • Handle interviews")
    print("  • Navigate complex forms")
    
    # Create diverse seekers
    examples = [
        {
            'name': 'College educated, employed',
            'cps': {'education': 'bachelors', 'employed': 1, 'AGE': 35}
        },
        {
            'name': 'High school, employed',
            'cps': {'education': 'high_school', 'employed': 1, 'AGE': 35}
        },
        {
            'name': 'Less than HS, unemployed',
            'cps': {'education': 'less_than_hs', 'employed': 0, 'AGE': 28}
        },
        {
            'name': 'Graduate degree, age 55',
            'cps': {'education': 'graduate', 'employed': 1, 'AGE': 55}
        },
    ]
    
    print(f"\n  {'Profile':<35} | {'Points':>7}")
    print(f"  {'-'*35}-+-{'-'*7}")
    
    for i, ex in enumerate(examples):
        seeker = Seeker(i, 'White', 20000, county='TEST', cps_data=ex['cps'],
                       random_state=np.random.RandomState(i))
        print(f"  {ex['name']:<35} | {seeker.bureaucracy_navigation_points:>7.1f}")
    
    print(f"\n  → More educated/employed = more points")
    print(f"  → Better able to withstand investigation")


def demo_investigation_actions():
    """Show investigation actions and costs."""
    print("\n" + "=" * 70)
    print("INVESTIGATION ACTIONS & COSTS")
    print("=" * 70)
    
    print(f"\n  {'Action':<30} | {'Cost (Honest)':>14} | {'Cost (Fraud)':>13}")
    print(f"  {'-'*30}-+-{'-'*14}-+-{'-'*13}")
    
    for action, details in Reviewer.INVESTIGATION_ACTIONS.items():
        cost = details['cost']
        fraud_cost = cost * Reviewer.FRAUD_COST_MULTIPLIER
        print(f"  {action:<30} | {cost:>14.0f} | {fraud_cost:>13.0f}")
    
    print(f"\n  Fraud multiplier: {Reviewer.FRAUD_COST_MULTIPLIER}x")
    print(f"  → Fraudsters pay double (maintaining lies is harder)")


def demo_honest_educated_passes():
    """Show educated honest person passing investigation."""
    print("\n" + "=" * 70)
    print("SCENARIO 1: Educated, Honest Person")
    print("=" * 70)
    
    # Create educated, employed, honest seeker
    cps_data = {'education': 'bachelors', 'employed': 1, 'AGE': 40}
    seeker = Seeker(1, 'White', 22000, county='TEST', cps_data=cps_data,
                   random_state=np.random.RandomState(42))
    
    print(f"\nSeeker Profile:")
    print(f"  Education: Bachelor's")
    print(f"  Employed: Yes")
    print(f"  Bureaucracy points: {seeker.bureaucracy_navigation_points:.1f}")
    
    # Create honest application with minor discrepancy (honest error)
    app = Application(
        application_id=1, seeker_id=1, program='SNAP', month=1,
        reported_income=21000, reported_household_size=2, reported_has_disability=False,
        true_income=22000, true_household_size=2, true_has_disability=False,
        is_error=True  # Honest error
    )
    app.suspicion_score = 0.6  # Moderate suspicion
    app.complexity = 0.4
    
    # Review
    reviewer = Reviewer(1, random_state=np.random.RandomState(42))
    reviewer.reset_monthly_capacity(1)
    
    print(f"\nInvestigation:")
    actions = reviewer._select_investigation_actions(app)
    print(f"  Actions selected: {actions}")
    
    # Simulate point deduction
    remaining = seeker.bureaucracy_navigation_points
    print(f"\n  Starting points: {remaining:.1f}")
    
    for action in actions:
        cost = Reviewer.INVESTIGATION_ACTIONS[action]['cost']
        if app.is_fraud:
            cost *= Reviewer.FRAUD_COST_MULTIPLIER
        remaining -= cost
        print(f"  After {action}: {remaining:.1f} points")
        
        if remaining < 0:
            print(f"  → FRAUD DETECTED")
            break
    
    if remaining >= 0:
        print(f"  → PASSED (points remaining: {remaining:.1f})")
    
    decision = reviewer.review_application(app, seeker=seeker)
    print(f"\nDecision: {decision}")


def demo_uneducated_fraudster_caught():
    """Show less educated fraudster getting caught."""
    print("\n" + "=" * 70)
    print("SCENARIO 2: Less Educated Fraudster")
    print("=" * 70)
    
    # Create less educated, unemployed fraudster
    cps_data = {'education': 'less_than_hs', 'employed': 0, 'AGE': 26}
    seeker = Seeker(2, 'Black', 15000, county='TEST', cps_data=cps_data,
                   random_state=np.random.RandomState(99))
    seeker.fraud_propensity = 1.8  # High fraud propensity (reduces points)
    
    print(f"\nSeeker Profile:")
    print(f"  Education: Less than HS")
    print(f"  Employed: No")
    print(f"  Fraud propensity: High")
    print(f"  Bureaucracy points: {seeker.bureaucracy_navigation_points:.1f}")
    
    # Create fraudulent application
    app = Application(
        application_id=2, seeker_id=2, program='SNAP', month=1,
        reported_income=8000, reported_household_size=2, reported_has_disability=False,
        true_income=35000, true_household_size=2, true_has_disability=False,
        is_fraud=True
    )
    app.suspicion_score = 0.9  # High suspicion
    app.complexity = 0.5
    
    # Review
    reviewer = Reviewer(2, random_state=np.random.RandomState(42))
    reviewer.reset_monthly_capacity(1)
    
    print(f"\nInvestigation:")
    actions = reviewer._select_investigation_actions(app)
    print(f"  Actions selected: {actions}")
    
    # Simulate with fraud penalty
    remaining = seeker.bureaucracy_navigation_points
    print(f"\n  Starting points: {remaining:.1f}")
    
    for action in actions:
        base_cost = Reviewer.INVESTIGATION_ACTIONS[action]['cost']
        fraud_cost = base_cost * Reviewer.FRAUD_COST_MULTIPLIER
        print(f"  {action}: base {base_cost}, fraud penalty ×2 = {fraud_cost}")
        remaining -= fraud_cost
        print(f"    → Remaining: {remaining:.1f} points")
        
        if remaining < 0:
            print(f"  → FRAUD DETECTED!")
            break
    
    decision = reviewer.review_application(app, seeker=seeker)
    print(f"\nDecision: {decision}")


def demo_educated_fraudster_sophisticated():
    """Show educated fraudster (harder to catch)."""
    print("\n" + "=" * 70)
    print("SCENARIO 3: Educated Fraudster (Sophisticated)")
    print("=" * 70)
    
    # Educated, employed, but committing fraud
    cps_data = {'education': 'bachelors', 'employed': 1, 'AGE': 38}
    seeker = Seeker(3, 'Hispanic', 28000, county='TEST', cps_data=cps_data,
                   random_state=np.random.RandomState(77))
    seeker.fraud_propensity = 1.6  # Committing fraud
    
    print(f"\nSeeker Profile:")
    print(f"  Education: Bachelor's")
    print(f"  Employed: Yes")
    print(f"  Committing fraud: Yes")
    print(f"  Bureaucracy points: {seeker.bureaucracy_navigation_points:.1f}")
    print(f"  (High education offsets fraud penalty)")
    
    # Sophisticated fraud
    app = Application(
        application_id=3, seeker_id=3, program='SNAP', month=1,
        reported_income=20000, reported_household_size=2, reported_has_disability=False,
        true_income=35000, true_household_size=2, true_has_disability=False,
        is_fraud=True
    )
    app.suspicion_score = 0.75  # Moderately suspicious
    app.complexity = 0.45
    
    # Review
    reviewer = Reviewer(3, random_state=np.random.RandomState(42))
    reviewer.reset_monthly_capacity(1)
    
    print(f"\nInvestigation:")
    actions = reviewer._select_investigation_actions(app)
    
    remaining = seeker.bureaucracy_navigation_points
    print(f"\n  Starting points: {remaining:.1f}")
    
    for action in actions:
        base_cost = Reviewer.INVESTIGATION_ACTIONS[action]['cost']
        fraud_cost = base_cost * 2.0
        remaining -= fraud_cost
        print(f"  {action}: {fraud_cost:.0f} points → {remaining:.1f} remaining")
        
        if remaining < 0:
            print(f"  → CAUGHT!")
            break
    
    if remaining >= 0:
        print(f"  → PASSED (sophisticated fraud slipped through)")
    
    decision = reviewer.review_application(app, seeker=seeker)
    print(f"\nDecision: {decision}")
    print(f"  (Educated fraudsters harder to catch, but still possible)")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Bureaucracy Navigation Points System")
    print("="*70)
    print("\nNew investigation system:")
    print("  • Each seeker has 'bureaucracy navigation points'")
    print("  • Based on education, employment, age")
    print("  • Reviewer performs investigation actions")
    print("  • Each action costs points")
    print("  • Fraudsters pay DOUBLE (maintaining lies is hard)")
    print("  • Points < 0 → fraud detected")
    print("\nResult: Structural inequality creates disparities!")
    
    demo_point_generation()
    demo_investigation_actions()
    demo_honest_educated_passes()
    demo_uneducated_fraudster_caught()
    demo_educated_fraudster_sophisticated()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Insights:")
    print("  • Educated people withstand more scrutiny (even if honest)")
    print("  • Less educated struggle (even if honest) → false positives")
    print("  • Fraudsters pay double → easier to detect")
    print("  • But educated fraudsters harder to catch (sophisticated)")
    print("  • Disparities emerge from structural factors, not bias!")
    print("\nNext: Run pytest tests/test_bureaucracy_points.py -v")


if __name__ == "__main__":
    main()