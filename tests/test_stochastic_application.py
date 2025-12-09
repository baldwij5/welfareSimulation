"""
Tests for Stochastic Application Propensity

Tests the new probabilistic application decision model.

Run: pytest tests/test_stochastic_application.py -v

Expected: 10 tests pass
"""

import pytest
import sys
sys.path.insert(0, 'src')

import numpy as np
from core.seeker import Seeker


class TestApplicationPropensity:
    """Test propensity calculation."""
    
    def test_propensity_exists_and_in_range(self):
        """Propensity should be calculated and in [0, 1]."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=15000,
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        propensity = seeker.calculate_application_propensity('SNAP', month=0)
        
        assert 0.0 <= propensity <= 1.0, f"Propensity {propensity} out of range"
    
    def test_high_perceived_prob_gives_high_propensity(self):
        """High perceived probability should give high propensity."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=15000,
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # Set high belief
        seeker.perceived_approval_probability['SNAP'] = 0.90
        propensity_high = seeker.calculate_application_propensity('SNAP', month=0)
        
        # Set low belief
        seeker.perceived_approval_probability['SNAP'] = 0.30
        propensity_low = seeker.calculate_application_propensity('SNAP', month=0)
        
        assert propensity_high > propensity_low, \
               "Higher beliefs should give higher propensity"
    
    def test_desperation_increases_propensity(self):
        """Very low income should increase propensity (desperation)."""
        # Rich (relatively)
        rich_seeker = Seeker(
            seeker_id=1,
            race='White',
            income=24000,  # $2000/month
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # Poor (desperate)
        poor_seeker = Seeker(
            seeker_id=2,
            race='White',
            income=3000,  # $250/month - desperate!
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(43)
        )
        
        # Both have same low beliefs
        rich_seeker.perceived_approval_probability['SNAP'] = 0.20
        poor_seeker.perceived_approval_probability['SNAP'] = 0.20
        
        rich_propensity = rich_seeker.calculate_application_propensity('SNAP', 0)
        poor_propensity = poor_seeker.calculate_application_propensity('SNAP', 0)
        
        assert poor_propensity > rich_propensity, \
               "Desperation should increase propensity despite low beliefs"
    
    def test_children_increase_propensity(self):
        """Having children should increase propensity (need to feed kids)."""
        no_kids = Seeker(
            seeker_id=1,
            race='White',
            income=15000,
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        with_kids = Seeker(
            seeker_id=2,
            race='White',
            income=15000,
            county='Test',
            has_children=True,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(43)
        )
        
        no_kids_prop = no_kids.calculate_application_propensity('SNAP', 0)
        with_kids_prop = with_kids.calculate_application_propensity('SNAP', 0)
        
        assert with_kids_prop > no_kids_prop, \
               "Having children should increase propensity"
    
    def test_prior_success_increases_propensity(self):
        """Prior approvals should increase propensity (positive reinforcement)."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=15000,
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # No prior experience
        propensity_no_exp = seeker.calculate_application_propensity('SNAP', 0)
        
        # Simulate prior success
        seeker.num_applications = 3
        seeker.num_approvals = 2  # 67% success rate
        
        propensity_with_exp = seeker.calculate_application_propensity('SNAP', 0)
        
        assert propensity_with_exp > propensity_no_exp, \
               "Prior success should increase propensity"


class TestStochasticApplication:
    """Test stochastic application decision."""
    
    def test_should_apply_is_stochastic(self):
        """Same seeker in different months should make different decisions."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=15000,
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # Set moderate belief (neither certain to apply nor certain not to)
        seeker.perceived_approval_probability['SNAP'] = 0.50
        
        # Check many months
        decisions = [seeker.should_apply('SNAP', month) for month in range(100)]
        
        # Should have BOTH True and False (stochastic)
        assert True in decisions, "Should sometimes apply"
        assert False in decisions, "Should sometimes not apply"
        
        # Application rate should be roughly 50% (given 0.50 propensity)
        application_rate = sum(decisions) / len(decisions)
        assert 0.3 < application_rate < 0.7, \
               f"With moderate propensity, should apply ~50% of time (got {application_rate:.1%})"
    
    def test_same_month_gives_same_decision(self):
        """Same month should give same decision (reproducible)."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=15000,
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # Call twice for same month
        decision1 = seeker.should_apply('SNAP', month=5)
        decision2 = seeker.should_apply('SNAP', month=5)
        
        assert decision1 == decision2, "Same month should give same decision (reproducible)"
    
    def test_high_propensity_applies_most_months(self):
        """High propensity should lead to applying most months."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=3000,  # Very low → desperate
            county='Test',
            has_children=True,  # Has kids → more desperate
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # High belief
        seeker.perceived_approval_probability['SNAP'] = 0.80
        
        # Should apply most months (high propensity)
        decisions = [seeker.should_apply('SNAP', month) for month in range(100)]
        application_rate = sum(decisions) / len(decisions)
        
        assert application_rate > 0.70, \
               f"High propensity should apply >70% of time (got {application_rate:.1%})"
    
    def test_low_propensity_rarely_applies(self):
        """Low propensity should lead to rarely applying."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=25000,  # High income → not desperate
            county='Test',
            has_children=False,  # No kids
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # Low belief (learned system doesn't work for them)
        seeker.perceived_approval_probability['SNAP'] = 0.15
        
        # Should rarely apply (low propensity)
        decisions = [seeker.should_apply('SNAP', month) for month in range(100)]
        application_rate = sum(decisions) / len(decisions)
        
        assert application_rate < 0.30, \
               f"Low propensity should apply <30% of time (got {application_rate:.1%})"
    
    def test_propensity_varies_across_months(self):
        """Propensity should vary slightly month-to-month (random component)."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=15000,
            county='Test',
            has_children=False,
            has_disability=False,
            cps_data={},
            random_state=np.random.RandomState(42)
        )
        
        # Calculate propensity for many months
        propensities = [
            seeker.calculate_application_propensity('SNAP', month)
            for month in range(50)
        ]
        
        # Should have variation (random component)
        assert len(set(propensities)) > 10, \
               "Propensity should vary across months"
        assert np.std(propensities) > 0.05, \
               "Should have meaningful variation"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])