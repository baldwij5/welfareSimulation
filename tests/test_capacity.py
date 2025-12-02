"""
Tests for Capacity System (Steps 3-5)

Tests evaluator and reviewer capacity tracking with complexity units.
Run with: pytest tests/test_capacity.py -v
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
from core.evaluator import Evaluator
from core.reviewer import Reviewer


@pytest.mark.unit
class TestEvaluatorCapacity:
    """Tests for evaluator capacity tracking."""
    
    def test_evaluator_has_monthly_capacity(self):
        """Test that evaluator has monthly_capacity attribute."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        assert hasattr(evaluator, 'monthly_capacity')
        assert evaluator.monthly_capacity > 0
    
    def test_evaluator_has_capacity_used(self):
        """Test that evaluator tracks capacity used."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        assert hasattr(evaluator, 'capacity_used_this_month')
        assert evaluator.capacity_used_this_month == 0.0
    
    def test_reset_monthly_capacity(self):
        """Test that reset_monthly_capacity resets usage."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        evaluator.capacity_used_this_month = 15.0
        
        evaluator.reset_monthly_capacity(month=2)
        
        assert evaluator.capacity_used_this_month == 0.0
        assert evaluator.current_month == 2
    
    def test_can_process_with_capacity(self):
        """Test can_process returns True when capacity available."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        evaluator.monthly_capacity = 20.0
        evaluator.capacity_used_this_month = 10.0
        
        # Create application with complexity 5.0
        app = Application(
            application_id=1,
            seeker_id=1,
            program='SNAP',
            month=1,
            reported_income=20000,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=20000,
            true_household_size=2,
            true_has_disability=False
        )
        app.complexity = 5.0
        
        assert evaluator.can_process(app) == True  # 10 remaining >= 5 needed
    
    def test_can_process_without_capacity(self):
        """Test can_process returns False when at capacity."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        evaluator.monthly_capacity = 20.0
        evaluator.capacity_used_this_month = 19.5
        
        # Create complex application
        app = Application(
            application_id=1,
            seeker_id=1,
            program='SSI',
            month=1,
            reported_income=15000,
            reported_household_size=2,
            reported_has_disability=True,
            true_income=15000,
            true_household_size=2,
            true_has_disability=True
        )
        app.complexity = 1.0
        
        assert evaluator.can_process(app) == False  # 0.5 remaining < 1.0 needed
    
    def test_use_capacity_deducts(self):
        """Test that use_capacity deducts from available capacity."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        evaluator.monthly_capacity = 20.0
        evaluator.capacity_used_this_month = 5.0
        
        app = Application(
            application_id=1,
            seeker_id=1,
            program='SNAP',
            month=1,
            reported_income=20000,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=20000,
            true_household_size=2,
            true_has_disability=False
        )
        app.complexity = 3.0
        
        evaluator.use_capacity(app)
        
        assert evaluator.capacity_used_this_month == 8.0  # 5.0 + 3.0
    
    def test_process_returns_capacity_exceeded(self):
        """Test that process_application returns CAPACITY_EXCEEDED when full."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        evaluator.monthly_capacity = 1.0
        evaluator.capacity_used_this_month = 0.8
        
        # Complex application that won't fit
        app = Application(
            application_id=1,
            seeker_id=1,
            program='SSI',
            month=1,
            reported_income=15000,
            reported_household_size=2,
            reported_has_disability=True,
            true_income=15000,
            true_household_size=2,
            true_has_disability=True
        )
        app.complexity = 1.0
        
        decision = evaluator.process_application(app)
        
        assert decision == "CAPACITY_EXCEEDED"


@pytest.mark.unit
class TestReviewerCapacity:
    """Tests for reviewer capacity tracking."""
    
    def test_reviewer_has_monthly_capacity(self):
        """Test that reviewer has monthly_capacity attribute."""
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        assert hasattr(reviewer, 'monthly_capacity')
        assert reviewer.monthly_capacity > 0
    
    def test_reviewer_tracks_capacity_used(self):
        """Test that reviewer tracks complexity units used."""
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        assert hasattr(reviewer, 'capacity_used_this_month')
        assert reviewer.capacity_used_this_month == 0.0
    
    def test_can_review_with_application(self):
        """Test can_review checks application complexity."""
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        reviewer.monthly_capacity = 10.0
        reviewer.capacity_used_this_month = 8.0
        
        # Simple application
        app = Application(
            application_id=1,
            seeker_id=1,
            program='SNAP',
            month=1,
            reported_income=20000,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=20000,
            true_household_size=2,
            true_has_disability=False
        )
        app.complexity = 1.5
        
        assert reviewer.can_review(app) == True  # 2.0 remaining >= 1.5 needed
    
    def test_can_review_at_capacity(self):
        """Test can_review returns False at capacity."""
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        reviewer.monthly_capacity = 10.0
        reviewer.capacity_used_this_month = 9.5
        
        # Complex application
        app = Application(
            application_id=1,
            seeker_id=1,
            program='SSI',
            month=1,
            reported_income=15000,
            reported_household_size=2,
            reported_has_disability=True,
            true_income=15000,
            true_household_size=2,
            true_has_disability=True
        )
        app.complexity = 1.0
        
        assert reviewer.can_review(app) == False  # 0.5 remaining < 1.0 needed
    
    def test_review_deducts_capacity(self):
        """Test that reviewing deducts complexity units."""
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        reviewer.monthly_capacity = 10.0
        reviewer.capacity_used_this_month = 3.0
        reviewer.reset_monthly_capacity(1)
        
        app = Application(
            application_id=1,
            seeker_id=1,
            program='SNAP',
            month=1,
            reported_income=8000,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=20000,  # Fraud!
            true_household_size=2,
            true_has_disability=False,
            is_fraud=True
        )
        app.complexity = 0.5
        
        # Before review
        assert reviewer.capacity_used_this_month == 0.0
        
        # Review
        decision = reviewer.review_application(app)
        
        # After review
        assert reviewer.capacity_used_this_month == 0.5


@pytest.mark.unit  
class TestPopulationBasedCapacity:
    """Tests for population-based capacity calculation."""
    
    def test_small_county_has_less_capacity(self):
        """Test that small counties have less capacity than large."""
        from simulation.runner import calculate_evaluator_capacity
        
        small_capacity = calculate_evaluator_capacity(50000)  # 50k pop
        large_capacity = calculate_evaluator_capacity(500000)  # 500k pop
        
        assert large_capacity > small_capacity
        assert large_capacity / small_capacity == pytest.approx(10, rel=0.1)  # ~10x
    
    def test_reviewer_less_capacity_than_evaluator(self):
        """Test that reviewers have less capacity (more specialized)."""
        from simulation.runner import calculate_evaluator_capacity, calculate_reviewer_capacity
        
        pop = 100000
        eval_cap = calculate_evaluator_capacity(pop)
        rev_cap = calculate_reviewer_capacity(pop)
        
        # Reviewers should have less capacity (same staff but fewer units)
        assert rev_cap < eval_cap
    
    def test_capacity_scales_linearly(self):
        """Test that capacity scales linearly with population."""
        from simulation.runner import calculate_evaluator_capacity
        
        cap_100k = calculate_evaluator_capacity(100000)
        cap_200k = calculate_evaluator_capacity(200000)
        
        assert cap_200k / cap_100k == pytest.approx(2.0, rel=0.01)


@pytest.mark.integration
class TestCapacityIntegration:
    """Integration tests for complete capacity system."""
    
    def test_small_county_hits_capacity(self):
        """Test that small counties can hit capacity limits."""
        from simulation.runner import create_population, create_evaluators, create_reviewers, run_month
        from data.data_loader import load_acs_county_data
        
        # Load ACS for population data
        acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
        
        # Small county
        counties = ['Autauga County, Alabama']
        
        # Create seekers (many eligible)
        seekers = []
        for i in range(100):
            seeker = Seeker(i, 'White', 15000, county=counties[0], has_children=True,
                          random_state=np.random.RandomState(i))
            seekers.append(seeker)
        
        # Create staff with population-based capacity
        evaluators = create_evaluators(counties, acs_data=acs, random_seed=42)
        reviewers = create_reviewers(counties, acs_data=acs, random_seed=42)
        
        # Run one busy month
        stats = run_month(seekers, evaluators, reviewers, month=0)
        
        # Should have some capacity exceeded (small county, many seekers)
        # This is realistic!
        assert 'applications_capacity_exceeded' in stats
    
    def test_capacity_resets_each_month(self):
        """Test that capacity resets properly each month."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        evaluator.monthly_capacity = 20.0
        
        # Use some capacity in month 1
        evaluator.reset_monthly_capacity(1)
        evaluator.capacity_used_this_month = 15.0
        
        # Reset for month 2
        evaluator.reset_monthly_capacity(2)
        
        # Should be back to 0
        assert evaluator.capacity_used_this_month == 0.0
        assert evaluator.current_month == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])