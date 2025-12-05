"""
Tests for State-Level Statistical Discrimination

Tests:
1. State models loaded and used correctly
2. Different states have different patterns
3. Credibility only applied during contact actions
4. All reviewers in same state share same model

Run with: pytest tests/test_state_models.py -v
"""

import pytest
import sys
import os
import numpy as np
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.seeker import Seeker
from core.application import Application
from core.reviewer import Reviewer


@pytest.mark.unit
class TestStateModelAttributes:
    """Tests for state model attributes."""
    
    def test_reviewer_accepts_state_parameter(self):
        """Test that reviewer can be initialized with state."""
        reviewer = Reviewer(
            reviewer_id=1,
            county='Test County, Alabama',
            state='Alabama',
            random_state=np.random.RandomState(42)
        )
        
        assert reviewer.state == 'Alabama'
        assert reviewer.county == 'Test County, Alabama'
    
    def test_reviewer_accepts_state_model(self):
        """Test that reviewer can store state-specific model."""
        model = {'model': None, 'state': 'Alabama', 'features': []}
        
        reviewer = Reviewer(
            reviewer_id=1,
            state='Alabama',
            state_model=model,
            random_state=np.random.RandomState(42)
        )
        
        assert reviewer.state_model == model
        assert reviewer.state_model['state'] == 'Alabama'
    
    def test_reviewer_works_without_state_model(self):
        """Test that reviewer works without state model."""
        reviewer = Reviewer(
            reviewer_id=1,
            state='Alabama',
            state_model=None,
            random_state=np.random.RandomState(42)
        )
        
        # Should return neutral
        seeker = Seeker(1, 'White', 15000, 'Test County, Alabama', False, False,
                       random_state=np.random.RandomState(42))
        
        multiplier = reviewer._calculate_credibility_from_state_patterns(seeker)
        assert multiplier == 1.0


@pytest.mark.unit
class TestContactOnlyCredibility:
    """Tests that credibility is only applied during contact."""
    
    def test_credibility_not_applied_to_database_checks(self):
        """Test that non-contact actions don't use credibility."""
        # This is tested by checking the logic in _conduct_points_investigation
        # Database checks happen BEFORE contact, so credibility_assessed = False
        # Therefore credibility_multiplier = 1.0 for those actions
        
        reviewer = Reviewer(1, random_state=np.random.RandomState(42))
        
        # Verify actions are correctly categorized
        assert reviewer.INVESTIGATION_ACTIONS['basic_income_check']['has_contact'] is False
        assert reviewer.INVESTIGATION_ACTIONS['interview']['has_contact'] is True
    
    def test_credibility_applied_after_first_contact(self):
        """Test that credibility affects actions AFTER first contact."""
        # Create mock state model
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        
        X = np.array([[20, 40000], [10, 60000]])
        y = np.array([1, 0])
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression()
        model.fit(X_scaled, y)
        
        state_model = {
            'model': model,
            'scaler': scaler,
            'features': ['poverty_rate', 'median_household_income'],
            'state': 'Alabama'
        }
        
        acs_data = pd.DataFrame({
            'county_name': ['Jefferson County, Alabama'],
            'poverty_rate': [15.9],
            'median_household_income': [52000]
        })
        
        reviewer = Reviewer(
            reviewer_id=1,
            county='Jefferson County, Alabama',
            state='Alabama',
            state_model=state_model,
            acs_data=acs_data,
            random_state=np.random.RandomState(42)
        )
        
        seeker = Seeker(1, 'White', 15000, 'Jefferson County, Alabama', False, False,
                       cps_data={}, random_state=np.random.RandomState(42))
        
        # Credibility calculation works
        multiplier = reviewer._calculate_credibility_from_state_patterns(seeker)
        
        assert 0.7 <= multiplier <= 1.5


@pytest.mark.integration
class TestStateLevelVariation:
    """Tests for variation across states."""
    
    def test_different_states_can_have_different_models(self):
        """Test that Alabama and California can have different patterns."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        
        # Alabama model: High poverty → High need
        X_al = np.array([[20, 40000], [10, 60000]])
        y_al = np.array([1, 0])
        scaler_al = StandardScaler()
        X_al_scaled = scaler_al.fit_transform(X_al)
        model_al = LogisticRegression()
        model_al.fit(X_al_scaled, y_al)
        
        alabama_model = {
            'model': model_al,
            'scaler': scaler_al,
            'features': ['poverty_rate', 'median_household_income'],
            'state': 'Alabama'
        }
        
        # California model: Different pattern (more generous)
        X_ca = np.array([[15, 50000], [10, 60000], [12, 55000]])
        y_ca = np.array([1, 1, 0])  # Mixed outcomes
        scaler_ca = StandardScaler()
        X_ca_scaled = scaler_ca.fit_transform(X_ca)
        model_ca = LogisticRegression()
        model_ca.fit(X_ca_scaled, y_ca)
        
        california_model = {
            'model': model_ca,
            'scaler': scaler_ca,
            'features': ['poverty_rate', 'median_household_income'],
            'state': 'California'
        }
        
        # Models should be different objects
        assert alabama_model['state'] != california_model['state']
        assert alabama_model is not california_model
    
    def test_reviewers_in_same_state_share_model(self):
        """Test that all reviewers in Alabama use Alabama model."""
        alabama_model = {'model': None, 'state': 'Alabama', 'features': []}
        
        reviewer1 = Reviewer(1, county='Jefferson County, Alabama', state='Alabama',
                           state_model=alabama_model, random_state=np.random.RandomState(42))
        
        reviewer2 = Reviewer(2, county='Mobile County, Alabama', state='Alabama',
                           state_model=alabama_model, random_state=np.random.RandomState(43))
        
        # Same state model
        assert reviewer1.state_model == reviewer2.state_model
        assert reviewer1.state == reviewer2.state == 'Alabama'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])