"""
Tests for Seeker Learning System

Tests how seekers learn from experience and adapt application behavior.

Run with: pytest tests/test_seeker_learning.py -v
"""

import pytest
import sys
import os
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.seeker import Seeker


@pytest.mark.unit
class TestLearningAttributes:
    """Tests for learning system attributes."""
    
    def test_seeker_has_learning_attributes(self):
        """Test that seekers have learning attributes."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, 
                       random_state=np.random.RandomState(42))
        
        assert hasattr(seeker, 'perceived_approval_probability')
        assert hasattr(seeker, 'application_threshold')
        assert hasattr(seeker, 'learning_rate')
        assert hasattr(seeker, 'application_outcomes')
    
    def test_initial_beliefs_are_optimistic(self):
        """Test that seekers start with optimistic beliefs."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        # Should start optimistic (>0.5)
        assert seeker.perceived_approval_probability['SNAP'] > 0.5
        assert seeker.perceived_approval_probability['TANF'] > 0.5
        assert seeker.perceived_approval_probability['SSI'] > 0.5
    
    def test_threshold_is_reasonable(self):
        """Test that application threshold is reasonable."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        # Should be between 0.1 and 0.5 (accounts for application costs)
        assert 0.1 <= seeker.application_threshold <= 0.5
    
    def test_learning_rate_in_range(self):
        """Test that learning rate is valid."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        # Should be 0-1
        assert 0.0 <= seeker.learning_rate <= 1.0


@pytest.mark.unit
class TestBeliefUpdating:
    """Tests for Bayesian belief updating."""
    
    def test_approval_increases_belief(self):
        """Test that approval increases perceived probability."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        initial_belief = seeker.perceived_approval_probability['SNAP']
        
        # Experience approval
        seeker.update_beliefs('SNAP', 'APPROVED')
        
        updated_belief = seeker.perceived_approval_probability['SNAP']
        
        # Should increase
        assert updated_belief > initial_belief
    
    def test_denial_decreases_belief(self):
        """Test that denial decreases perceived probability."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        initial_belief = seeker.perceived_approval_probability['SNAP']
        
        # Experience denial
        seeker.update_beliefs('SNAP', 'DENIED')
        
        updated_belief = seeker.perceived_approval_probability['SNAP']
        
        # Should decrease
        assert updated_belief < initial_belief
    
    def test_multiple_denials_compound(self):
        """Test that multiple denials progressively decrease belief."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        belief_0 = seeker.perceived_approval_probability['SNAP']
        
        seeker.update_beliefs('SNAP', 'DENIED')
        belief_1 = seeker.perceived_approval_probability['SNAP']
        
        seeker.update_beliefs('SNAP', 'DENIED')
        belief_2 = seeker.perceived_approval_probability['SNAP']
        
        seeker.update_beliefs('SNAP', 'DENIED')
        belief_3 = seeker.perceived_approval_probability['SNAP']
        
        # Should decrease progressively
        assert belief_0 > belief_1 > belief_2 > belief_3
    
    def test_capacity_exceeded_does_not_update(self):
        """Test that capacity issues don't update beliefs."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        initial_belief = seeker.perceived_approval_probability['SNAP']
        
        # Experience capacity issue (not about eligibility)
        seeker.update_beliefs('SNAP', 'CAPACITY_EXCEEDED')
        
        updated_belief = seeker.perceived_approval_probability['SNAP']
        
        # Should stay same (uninformative)
        assert updated_belief == initial_belief


@pytest.mark.unit
class TestLearningBasedDecisions:
    """Tests for learning-based application decisions."""
    
    def test_applies_when_belief_high(self):
        """Test that seekers apply when belief exceeds threshold."""
        seeker = Seeker(1, 'White', 1000, 'TEST', True, False,  # Income = $1k, has children
                       random_state=np.random.RandomState(42))
        
        # Set high belief
        seeker.perceived_approval_probability['TANF'] = 0.80  # 80% belief
        seeker.application_threshold = 0.25
        
        # Should apply (80% > 25%)
        assert seeker.should_apply('TANF', month=5) is True
    
    def test_does_not_apply_when_belief_low(self):
        """Test that seekers don't apply when belief below threshold."""
        seeker = Seeker(1, 'White', 1000, 'TEST', True, False,
                       random_state=np.random.RandomState(42))
        
        # Set low belief (learned from repeated denials)
        seeker.perceived_approval_probability['TANF'] = 0.15  # Only 15% belief
        seeker.application_threshold = 0.25
        
        # Should NOT apply (15% < 25%)
        assert seeker.should_apply('TANF', month=5) is False
    
    def test_learns_to_stop_applying_after_denials(self):
        """Test that seekers learn to stop applying after repeated denials."""
        seeker = Seeker(1, 'White', 1000, 'TEST', True, False,
                       random_state=np.random.RandomState(42))
        
        # Start optimistic
        assert seeker.should_apply('TANF', month=1) is True
        
        # Three denials
        seeker.update_beliefs('TANF', 'DENIED')
        seeker.update_beliefs('TANF', 'DENIED')
        seeker.update_beliefs('TANF', 'DENIED')
        
        # Should stop applying (belief dropped below threshold)
        belief = seeker.perceived_approval_probability['TANF']
        
        # After 3 denials with learning_rate=0.3:
        # 0.60 → 0.42 → 0.29 → 0.20
        assert belief < seeker.application_threshold
        assert seeker.should_apply('TANF', month=5) is False


@pytest.mark.integration
class TestLearningEffects:
    """Integration tests for learning effects on disparities."""
    
    def test_successful_seekers_keep_applying(self):
        """Test that successful seekers maintain high beliefs."""
        seeker = Seeker(1, 'White', 1500, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        initial_belief = seeker.perceived_approval_probability['SNAP']
        
        # Multiple approvals
        seeker.update_beliefs('SNAP', 'APPROVED')
        seeker.update_beliefs('SNAP', 'APPROVED')
        seeker.update_beliefs('SNAP', 'APPROVED')
        
        # Belief should increase
        final_belief = seeker.perceived_approval_probability['SNAP']
        assert final_belief > initial_belief
        
        # Should definitely still apply
        assert seeker.should_apply('SNAP', month=10) is True
    
    def test_discouraged_seekers_stop_trying(self):
        """Test discouraged worker effect - learn helplessness."""
        seeker = Seeker(1, 'White', 1500, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        # String of denials
        for _ in range(5):
            seeker.update_beliefs('SNAP', 'DENIED')
        
        # Should learn to stop trying
        assert seeker.should_apply('SNAP', month=10) is False
        
        # Check belief is very low
        assert seeker.perceived_approval_probability['SNAP'] < 0.20
    
    def test_learning_differs_by_program(self):
        """Test that beliefs update independently by program."""
        seeker = Seeker(1, 'White', 800, 'TEST', True, True,  # Eligible for all
                       random_state=np.random.RandomState(42))
        
        # SNAP: Get approved
        seeker.update_beliefs('SNAP', 'APPROVED')
        
        # TANF: Get denied
        seeker.update_beliefs('TANF', 'DENIED')
        
        # Beliefs should diverge
        snap_belief = seeker.perceived_approval_probability['SNAP']
        tanf_belief = seeker.perceived_approval_probability['TANF']
        
        assert snap_belief > tanf_belief  # SNAP higher (was approved)
    
    def test_get_success_rate_calculates_correctly(self):
        """Test that actual success rate is calculated from history."""
        seeker = Seeker(1, 'White', 1500, 'TEST', False, False,
                       random_state=np.random.RandomState(42))
        
        # No history yet
        assert seeker.get_success_rate('SNAP') is None
        
        # Add outcomes: 2 approved, 3 denied
        seeker.update_beliefs('SNAP', 'APPROVED')
        seeker.update_beliefs('SNAP', 'DENIED')
        seeker.update_beliefs('SNAP', 'APPROVED')
        seeker.update_beliefs('SNAP', 'DENIED')
        seeker.update_beliefs('SNAP', 'DENIED')
        
        # Success rate should be 2/5 = 0.4
        assert seeker.get_success_rate('SNAP') == 0.4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])