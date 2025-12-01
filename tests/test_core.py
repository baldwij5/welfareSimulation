"""
Tests for core simulation classes.

Run with: pytest tests/test_core.py -v
Or: pytest tests/ -v  (runs all tests)
"""

import sys
import os
import numpy as np
import pytest

# Add src to path (works from project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.seeker import Seeker
from core.application import Application
from core.evaluator import Evaluator
from core.reviewer import Reviewer


class TestSeeker:
    """Tests for Seeker class."""
    
    def test_seeker_creation(self):
        """Test that we can create a seeker."""
        seeker = Seeker(1, 'White', 50000, county='TEST', has_children=True, has_disability=False)
        
        assert seeker.id == 1
        assert seeker.race == 'White'
        assert seeker.income == 50000
        assert seeker.has_children == True
        assert seeker.has_disability == False
    
    def test_fraud_propensity_range(self):
        """Test that fraud propensity is between 0 and 2."""
        seekers = [Seeker(i, 'White', 50000, county='TEST', random_state=np.random.RandomState(i)) 
                   for i in range(100)]
        
        for seeker in seekers:
            assert 0 <= seeker.fraud_propensity <= 2
    
    def test_lying_magnitude_range(self):
        """Test that lying magnitude is between 0 and 100."""
        seekers = [Seeker(i, 'White', 50000, county='TEST', random_state=np.random.RandomState(i)) 
                   for i in range(100)]
        
        for seeker in seekers:
            assert 0 <= seeker.lying_magnitude <= 100
    
    def test_monthly_income_calculation(self):
        """Test that monthly income is correctly calculated."""
        seeker = Seeker(1, 'White', 60000, county='TEST')  # $60k annual = $5k monthly
        
        monthly = seeker.get_monthly_income()
        assert abs(monthly * 12 - seeker.income) < 1  # Allow rounding error
        assert monthly == 5000


class TestApplication:
    """Tests for Application class."""
    
    def test_application_creation(self):
        """Test that we can create an application."""
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
    
    def test_income_discrepancy_honest(self):
        """Test discrepancy calculation for honest application."""
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
        
        assert app.get_income_discrepancy() == 0
        assert app.get_income_discrepancy_pct() == 0
    
    def test_income_discrepancy_fraud(self):
        """Test discrepancy calculation for fraudulent application."""
        app = Application(
            application_id=2,
            seeker_id=102,
            program='SNAP',
            month=1,
            reported_income=20000,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=50000,
            true_household_size=2,
            true_has_disability=False,
            is_fraud=True
        )
        
        assert app.get_income_discrepancy() == 30000
        assert abs(app.get_income_discrepancy_pct() - 0.6) < 0.01  # 60%


class TestEvaluator:
    """Tests for Evaluator class."""
    
    def test_evaluator_creation(self):
        """Test that we can create an evaluator."""
        rng = np.random.RandomState(42)
        evaluator = Evaluator(1, county='TEST', program='SNAP', strictness=0.5, random_state=rng)
        
        assert evaluator.id == 1
        assert evaluator.county == 'TEST'
        assert evaluator.program == 'SNAP'
        assert evaluator.strictness == 0.5
        assert evaluator.applications_processed == 0
    
    def test_approve_eligible_application(self):
        """Test that eligible application gets approved."""
        rng = np.random.RandomState(42)
        evaluator = Evaluator(1, county='TEST', program='SNAP', strictness=0.5, random_state=rng)
        
        app = Application(
            application_id=1,
            seeker_id=101,
            program='SNAP',
            month=1,
            reported_income=24000,  # $2k/month - eligible
            reported_household_size=2,
            reported_has_disability=False,
            true_income=24000,
            true_household_size=2,
            true_has_disability=False
        )
        
        decision = evaluator.process_application(app)
        assert decision in ['APPROVED', 'ESCALATED']
        assert evaluator.applications_processed == 1
    
    def test_deny_ineligible_application(self):
        """Test that ineligible application gets denied."""
        rng = np.random.RandomState(42)
        evaluator = Evaluator(1, county='TEST', program='SNAP', strictness=0.5, random_state=rng)
        
        app = Application(
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
        
        decision = evaluator.process_application(app)
        assert decision == 'DENIED'
        assert not app.approved
    
    def test_ssi_escalation(self):
        """Test that SSI applications get escalated."""
        rng = np.random.RandomState(42)
        evaluator = Evaluator(1, county='TEST', program='SNAP', strictness=0.5, random_state=rng)
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


class TestReviewer:
    """Tests for Reviewer class."""
    
    def test_reviewer_creation(self):
        """Test that we can create a reviewer."""
        rng = np.random.RandomState(42)
        reviewer = Reviewer(1, capacity=50, accuracy=0.85, random_state=rng)
        
        assert reviewer.id == 1
        assert reviewer.capacity == 50
        assert reviewer.accuracy == 0.85
    
    def test_capacity_tracking(self):
        """Test that reviewer tracks monthly capacity."""
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
        
        # Should be at capacity
        assert not reviewer.can_review()
        assert reviewer.reviewed_this_month == 5
    
    def test_fraud_detection(self):
        """Test that reviewer detects most fraud."""
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
        # Should detect around 85% (allow some variance)
        assert 0.75 < detection_rate < 0.95, f"Detection rate: {detection_rate:.1%}"
    
    def test_honest_approval(self):
        """Test that reviewer approves most honest applications."""
        rng = np.random.RandomState(42)
        reviewer = Reviewer(1, capacity=100, accuracy=0.85, random_state=rng)
        reviewer.reset_monthly_capacity(1)
        
        # Create 100 honest applications
        approved = 0
        for i in range(100):
            app = Application(
                application_id=i,
                seeker_id=1000 + i,
                program='SNAP',
                month=1,
                reported_income=24000,
                reported_household_size=2,
                reported_has_disability=False,
                true_income=24000,
                true_household_size=2,
                true_has_disability=False,
                is_fraud=False
            )
            
            decision = reviewer.review_application(app)
            if decision == 'APPROVED':
                approved += 1
        
        approval_rate = approved / 100
        # Should approve most (allow some false positives)
        assert approval_rate > 0.80, f"Approval rate: {approval_rate:.1%}"

if __name__ == "__main__":
    # If running directly, use pytest
    import subprocess
    subprocess.run(["pytest", __file__, "-v"])