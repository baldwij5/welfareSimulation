"""
Manual test runner for core simulation classes.
Run with: python tests/run_tests.py
"""

import sys
import os
import numpy as np

# Add src to path (works from any directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.seeker import Seeker
from core.application import Application
from core.evaluator import Evaluator
from core.reviewer import Reviewer


def test_seeker_creation():
    """Test that we can create a seeker."""
    print("  Testing seeker creation...", end=" ")
    rng = np.random.RandomState(42)
    seeker = Seeker(1, 'White', rng)
    
    assert seeker.id == 1
    assert seeker.race == 'White'
    assert seeker.income > 0
    assert isinstance(seeker.has_children, bool)
    print("PASS")


def test_income_distributions():
    """Test that income distributions match Census targets."""
    print("  Testing income distributions...", end=" ")
    
    # White seekers
    white_incomes = [Seeker(i, 'White', np.random.RandomState(i)).income 
                     for i in range(1000)]
    white_median = np.median(white_incomes)
    assert 60000 < white_median < 95000, f"White median: ${white_median:,.0f}"
    
    # Black seekers
    black_incomes = [Seeker(i, 'Black', np.random.RandomState(i)).income 
                     for i in range(1000)]
    black_median = np.median(black_incomes)
    assert 38000 < black_median < 60000, f"Black median: ${black_median:,.0f}"
    
    # Gap should exist
    gap = white_median - black_median
    assert gap > 15000, f"Gap too small: ${gap:,.0f}"
    
    print(f"PASS (White: ${white_median:,.0f}, Black: ${black_median:,.0f}, Gap: ${gap:,.0f})")


def test_application_creation():
    """Test that we can create an application."""
    print("  Testing application creation...", end=" ")
    
    app = Application(
        application_id=1,
        seeker_id=101,
        program='SNAP',
        month=1,
        reported_income=30000,
        reported_household_size=2,
        reported_has_disability=False,
        true_income=30000,
        true_household_size=2,
        true_has_disability=False
    )
    
    assert app.application_id == 1
    assert app.program == 'SNAP'
    assert not app.is_fraud
    assert app.get_income_discrepancy() == 0
    print("PASS")


def test_evaluator_processing():
    """Test that evaluator can process applications."""
    print("  Testing evaluator processing...", end=" ")
    
    rng = np.random.RandomState(42)
    evaluator = Evaluator(1, strictness=0.5, random_state=rng)
    
    # Eligible application
    app1 = Application(
        application_id=1,
        seeker_id=101,
        program='SNAP',
        month=1,
        reported_income=24000,  # Eligible
        reported_household_size=2,
        reported_has_disability=False,
        true_income=24000,
        true_household_size=2,
        true_has_disability=False
    )
    
    decision1 = evaluator.process_application(app1)
    assert decision1 in ['APPROVED', 'ESCALATED']
    
    # Ineligible application
    app2 = Application(
        application_id=2,
        seeker_id=102,
        program='SNAP',
        month=1,
        reported_income=100000,  # Too high
        reported_household_size=2,
        reported_has_disability=False,
        true_income=100000,
        true_household_size=2,
        true_has_disability=False
    )
    
    decision2 = evaluator.process_application(app2)
    assert decision2 == 'DENIED'
    assert not app2.approved
    
    print("PASS")


def test_ssi_escalation():
    """Test that SSI applications get escalated to reviewer."""
    print("  Testing SSI escalation...", end=" ")
    
    rng = np.random.RandomState(42)
    evaluator = Evaluator(1, strictness=0.5, random_state=rng)
    reviewer = Reviewer(1, capacity=50, accuracy=0.85, random_state=rng)
    
    app = Application(
        application_id=3,
        seeker_id=103,
        program='SSI',
        month=1,
        reported_income=18000,
        reported_household_size=1,
        reported_has_disability=True,
        true_income=18000,
        true_household_size=1,
        true_has_disability=True
    )
    
    decision = evaluator.process_application(app, reviewer=reviewer)
    assert decision == 'ESCALATED'
    assert app.escalated_to_reviewer
    print("PASS")


def test_reviewer_capacity():
    """Test that reviewer tracks capacity correctly."""
    print("  Testing reviewer capacity...", end=" ")
    
    rng = np.random.RandomState(42)
    reviewer = Reviewer(1, capacity=5, accuracy=0.85, random_state=rng)
    reviewer.reset_monthly_capacity(1)
    
    assert reviewer.can_review()
    
    # Review 5 applications
    for i in range(5):
        app = Application(
            application_id=i,
            seeker_id=100 + i,
            program='SNAP',
            month=1,
            reported_income=24000,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=24000,
            true_household_size=2,
            true_has_disability=False
        )
        reviewer.review_application(app)
    
    assert not reviewer.can_review()
    assert reviewer.reviewed_this_month == 5
    print("PASS")


def test_reviewer_fraud_detection():
    """Test that reviewer detects fraud at expected rate."""
    print("  Testing reviewer fraud detection...", end=" ")
    
    rng = np.random.RandomState(42)
    reviewer = Reviewer(1, capacity=100, accuracy=0.85, random_state=rng)
    reviewer.reset_monthly_capacity(1)
    
    # Create 100 fraudulent applications
    fraud_detected = 0
    for i in range(100):
        app = Application(
            application_id=i,
            seeker_id=1000 + i,
            program='SNAP',
            month=1,
            reported_income=10000,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=50000,
            true_household_size=2,
            true_has_disability=False,
            is_fraud=True
        )
        
        decision = reviewer.review_application(app)
        if decision == 'DENIED':
            fraud_detected += 1
    
    detection_rate = fraud_detected / 100
    assert 0.75 < detection_rate < 0.95, f"Detection rate: {detection_rate:.1%}"
    print(f"PASS (detected {detection_rate:.1%})")


def test_end_to_end_workflow():
    """Test complete workflow: Seeker -> Application -> Evaluator -> Reviewer."""
    print("  Testing end-to-end workflow...", end=" ")
    
    rng = np.random.RandomState(42)
    
    # Create seeker
    seeker = Seeker(1, 'Black', random_state=rng)
    
    # Create application (honest)
    app = Application(
        application_id=1,
        seeker_id=seeker.id,
        program='SNAP',
        month=1,
        reported_income=seeker.income,
        reported_household_size=2,
        reported_has_disability=seeker.has_disability,
        true_income=seeker.income,
        true_household_size=2,
        true_has_disability=seeker.has_disability
    )
    
    # Process with evaluator
    evaluator = Evaluator(1, strictness=0.5, random_state=rng)
    reviewer = Reviewer(1, capacity=50, accuracy=0.85, random_state=rng)
    reviewer.reset_monthly_capacity(1)
    
    decision = evaluator.process_application(app, reviewer=reviewer)
    
    # If escalated, reviewer processes
    if decision == 'ESCALATED':
        final_decision = reviewer.review_application(app)
        assert final_decision in ['APPROVED', 'DENIED']
    else:
        assert decision in ['APPROVED', 'DENIED']
    
    print("PASS")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("Running Core Simulation Tests")
    print("="*60 + "\n")
    
    tests = [
        ("Seeker Creation", test_seeker_creation),
        ("Income Distributions", test_income_distributions),
        ("Application Creation", test_application_creation),
        ("Evaluator Processing", test_evaluator_processing),
        ("SSI Escalation", test_ssi_escalation),
        ("Reviewer Capacity", test_reviewer_capacity),
        ("Reviewer Fraud Detection", test_reviewer_fraud_detection),
        ("End-to-End Workflow", test_end_to_end_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  {test_name}... FAIL")
            print(f"    Error: {e}")
            failed += 1
        except Exception as e:
            print(f"  {test_name}... ERROR")
            print(f"    Error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)