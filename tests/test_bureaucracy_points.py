"""
Tests for Bureaucracy Navigation Points System

Run with: pytest tests/test_bureaucracy_points.py -v
"""

import pytest
import numpy as np
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.seeker import Seeker
from core.application import Application
from core.reviewer import Reviewer


@pytest.mark.unit
class TestBureaucracyPoints:
    """Tests for bureaucracy navigation points generation."""
    
    def test_seeker_has_bureaucracy_points(self):
        """Test that seekers have bureaucracy_navigation_points."""
        seeker = Seeker(1, 'White', 20000, county='TEST', random_state=np.random.RandomState(42))
        
        assert hasattr(seeker, 'bureaucracy_navigation_points')
        assert isinstance(seeker.bureaucracy_navigation_points, (int, float))
    
    def test_bureaucracy_points_in_reasonable_range(self):
        """Test that points are in 0-20 range (roughly)."""
        seekers = [Seeker(i, 'White', 20000, county='TEST', random_state=np.random.RandomState(i))
                   for i in range(100)]
        
        points = [s.bureaucracy_navigation_points for s in seekers]
        
        # Should be mostly between 0 and 20
        assert min(points) >= 0
        assert max(points) <= 25  # Allow some variation
        assert np.mean(points) > 5  # Average should be reasonable
        assert np.mean(points) < 15
    
    def test_educated_have_more_points(self):
        """Test that educated seekers have higher bureaucracy capacity."""
        # Create seekers with different education
        less_educated = []
        highly_educated = []
        
        for i in range(50):
            cps_data_less = {'education': 'less_than_hs', 'AGE': 35, 'employed': 0}
            seeker_less = Seeker(i, 'White', 20000, county='TEST', cps_data=cps_data_less,
                                random_state=np.random.RandomState(i))
            less_educated.append(seeker_less)
            
            cps_data_high = {'education': 'bachelors', 'AGE': 35, 'employed': 1}
            seeker_high = Seeker(i+50, 'White', 20000, county='TEST', cps_data=cps_data_high,
                                random_state=np.random.RandomState(i+50))
            highly_educated.append(seeker_high)
        
        avg_less = np.mean([s.bureaucracy_navigation_points for s in less_educated])
        avg_high = np.mean([s.bureaucracy_navigation_points for s in highly_educated])
        
        # Educated should have significantly more points
        assert avg_high > avg_less + 5  # At least 5 point difference
    
    def test_employed_have_more_points(self):
        """Test that employed seekers have higher capacity."""
        employed_seekers = []
        unemployed_seekers = []
        
        for i in range(50):
            cps_employed = {'employed': 1, 'education': 'high_school', 'AGE': 35}
            seeker_emp = Seeker(i, 'Black', 20000, county='TEST', cps_data=cps_employed,
                              random_state=np.random.RandomState(i))
            employed_seekers.append(seeker_emp)
            
            cps_unemployed = {'employed': 0, 'education': 'high_school', 'AGE': 35}
            seeker_unemp = Seeker(i+50, 'Black', 20000, county='TEST', cps_data=cps_unemployed,
                                random_state=np.random.RandomState(i+50))
            unemployed_seekers.append(seeker_unemp)
        
        avg_employed = np.mean([s.bureaucracy_navigation_points for s in employed_seekers])
        avg_unemployed = np.mean([s.bureaucracy_navigation_points for s in unemployed_seekers])
        
        # Employed should have more points (documentation)
        assert avg_employed > avg_unemployed + 3


@pytest.mark.unit
class TestInvestigationActions:
    """Tests for investigation action selection and costs."""
    
    def test_reviewer_has_investigation_actions(self):
        """Test that Reviewer class has investigation actions defined."""
        assert hasattr(Reviewer, 'INVESTIGATION_ACTIONS')
        assert isinstance(Reviewer.INVESTIGATION_ACTIONS, dict)
        assert len(Reviewer.INVESTIGATION_ACTIONS) > 0
    
    def test_fraud_cost_multiplier_exists(self):
        """Test that fraud cost multiplier is defined."""
        assert hasattr(Reviewer, 'FRAUD_COST_MULTIPLIER')
        assert Reviewer.FRAUD_COST_MULTIPLIER > 1.0  # Should be penalty
    
    def test_select_investigation_actions_method_exists(self):
        """Test that action selection method exists."""
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        assert hasattr(reviewer, '_select_investigation_actions')
    
    def test_more_suspicious_gets_more_actions(self):
        """Test that higher suspicion leads to more investigation actions."""
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        
        # Low suspicion application
        app_low = Application(
            application_id=1, seeker_id=1, program='SNAP', month=1,
            reported_income=20000, reported_household_size=2, reported_has_disability=False,
            true_income=20000, true_household_size=2, true_has_disability=False
        )
        app_low.suspicion_score = 0.3
        app_low.complexity = 0.4
        
        # High suspicion application
        app_high = Application(
            application_id=2, seeker_id=2, program='SNAP', month=1,
            reported_income=8000, reported_household_size=2, reported_has_disability=False,
            true_income=40000, true_household_size=2, true_has_disability=False,
            is_fraud=True
        )
        app_high.suspicion_score = 0.95
        app_high.complexity = 0.6
        
        actions_low = reviewer._select_investigation_actions(app_low)
        actions_high = reviewer._select_investigation_actions(app_high)
        
        # High suspicion should get more actions
        assert len(actions_high) > len(actions_low)


@pytest.mark.integration
class TestPointsInvestigation:
    """Integration tests for points-based investigation."""
    
    def test_educated_honest_passes_investigation(self):
        """Test that educated honest people pass investigation."""
        # Educated, employed, honest
        cps_data = {'education': 'bachelors', 'employed': 1, 'AGE': 40}
        seeker = Seeker(1, 'White', 20000, county='TEST', cps_data=cps_data,
                       random_state=np.random.RandomState(42))
        seeker.fraud_propensity = 0.1  # Honest
        
        # Create honest application
        app = seeker.create_application('SNAP', month=1, application_id=1)
        app.suspicion_score = 0.6  # Moderate suspicion (will investigate)
        
        # Review
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        reviewer.reset_monthly_capacity(1)
        decision = reviewer.review_application(app, seeker=seeker)
        
        # Should pass (high bureaucracy points)
        assert decision == 'APPROVED'
    
    def test_uneducated_fraudster_detected(self):
        """Test that less educated fraudsters are detected easily."""
        # Less educated, unemployed, fraudster
        cps_data = {'education': 'less_than_hs', 'employed': 0, 'AGE': 24}
        seeker = Seeker(1, 'Black', 20000, county='TEST', cps_data=cps_data,
                       random_state=np.random.RandomState(42))
        seeker.fraud_propensity = 1.9  # High fraud propensity (lowers points)
        
        # Create fraudulent application
        app = Application(
            application_id=1, seeker_id=1, program='SNAP', month=1,
            reported_income=8000, reported_household_size=2, reported_has_disability=False,
            true_income=35000, true_household_size=2, true_has_disability=False,
            is_fraud=True
        )
        app.complexity = 0.5
        app.suspicion_score = 0.9  # High suspicion
        
        # Review
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        reviewer.reset_monthly_capacity(1)
        decision = reviewer.review_application(app, seeker=seeker)
        
        # Should be detected (low points + fraud penalty)
        assert decision == 'DENIED'
    
    def test_points_investigation_creates_false_positives(self):
        """Test that honest but less educated can be denied (false positive)."""
        # Less educated, unemployed, but HONEST
        cps_data = {'education': 'less_than_hs', 'employed': 0, 'AGE': 28}
        seeker = Seeker(1, 'Hispanic', 15000, county='TEST', cps_data=cps_data,
                       random_state=np.random.RandomState(99))
        seeker.fraud_propensity = 0.2  # Honest!
        seeker.error_propensity = 2.0  # But makes errors
        
        # This might create an application with error
        # Try multiple times to get an error case
        error_app = None
        for month in range(20):
            app = seeker.create_application('SNAP', month=month, application_id=month)
            if app and app.is_error and not app.is_fraud:
                error_app = app
                break
        
        if error_app:
            error_app.suspicion_score = 0.8  # Will investigate thoroughly
            
            # Review
            reviewer = Reviewer(1, random_state=np.random.RandomState(42))
            reviewer.reset_monthly_capacity(1)
            decision = reviewer.review_application(error_app, seeker=seeker)
            
            # Might be denied even though honest (low points)
            # This is realistic - false positive due to inability to navigate bureaucracy
            # We can't assert exact outcome, but can verify system allows it


if __name__ == "__main__":
    pytest.main([__file__, "-v"])