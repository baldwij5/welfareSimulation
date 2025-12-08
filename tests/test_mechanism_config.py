"""
Unit Tests for MechanismConfig

Tests the mechanism configuration framework that controls which
theoretical mechanisms are active during ablation studies.

Run: pytest tests/test_mechanism_config.py -v

Expected: 7 tests pass (after implementing mechanism_config.py)
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from core.mechanism_config import MechanismConfig


class TestMechanismConfig:
    """Test mechanism configuration framework."""
    
    def test_baseline_has_no_mechanisms(self):
        """Baseline should disable all mechanisms."""
        config = MechanismConfig.baseline()
        
        assert config.count_active() == 0, "Baseline should have 0 active mechanisms"
        assert config.get_active_mechanisms() == [], "Baseline should return empty list"
        assert config.bureaucracy_points_enabled == False
        assert config.fraud_history_enabled == False
        assert config.learning_enabled == False
        assert config.state_discrimination_enabled == False
    
    def test_full_model_has_all_mechanisms(self):
        """Full model should enable all 4 mechanisms."""
        config = MechanismConfig.full_model()
        
        assert config.count_active() == 4, "Full model should have 4 active mechanisms"
        assert len(config.get_active_mechanisms()) == 4
        assert config.bureaucracy_points_enabled == True
        assert config.fraud_history_enabled == True
        assert config.learning_enabled == True
        assert config.state_discrimination_enabled == True
    
    def test_only_bureaucracy_has_one_mechanism(self):
        """Only bureaucracy config should have exactly 1 mechanism."""
        config = MechanismConfig.only_bureaucracy()
        
        assert config.count_active() == 1, "Should have exactly 1 mechanism"
        assert config.get_active_mechanisms() == ['bureaucracy_points']
        assert config.bureaucracy_points_enabled == True
        assert config.fraud_history_enabled == False
        assert config.learning_enabled == False
        assert config.state_discrimination_enabled == False
    
    def test_only_fraud_has_one_mechanism(self):
        """Only fraud config should have exactly 1 mechanism."""
        config = MechanismConfig.only_fraud()
        
        assert config.count_active() == 1
        assert config.get_active_mechanisms() == ['fraud_history']
        assert config.bureaucracy_points_enabled == False
        assert config.fraud_history_enabled == True
        assert config.learning_enabled == False
        assert config.state_discrimination_enabled == False
    
    def test_only_learning_has_one_mechanism(self):
        """Only learning config should have exactly 1 mechanism."""
        config = MechanismConfig.only_learning()
        
        assert config.count_active() == 1
        assert config.get_active_mechanisms() == ['learning']
        assert config.bureaucracy_points_enabled == False
        assert config.fraud_history_enabled == False
        assert config.learning_enabled == True
        assert config.state_discrimination_enabled == False
    
    def test_only_state_discrimination_has_one_mechanism(self):
        """Only state discrimination config should have exactly 1 mechanism."""
        config = MechanismConfig.only_state_discrimination()
        
        assert config.count_active() == 1
        assert config.get_active_mechanisms() == ['state_discrimination']
        assert config.bureaucracy_points_enabled == False
        assert config.fraud_history_enabled == False
        assert config.learning_enabled == False
        assert config.state_discrimination_enabled == True
    
    def test_custom_config(self):
        """Test custom configuration with multiple mechanisms."""
        config = MechanismConfig(
            bureaucracy_points_enabled=True,
            fraud_history_enabled=True,
            learning_enabled=False,
            state_discrimination_enabled=False
        )
        
        assert config.count_active() == 2
        assert 'bureaucracy_points' in config.get_active_mechanisms()
        assert 'fraud_history' in config.get_active_mechanisms()
        assert 'learning' not in config.get_active_mechanisms()
        assert 'state_discrimination' not in config.get_active_mechanisms()
    
    def test_config_equality(self):
        """Test that config equality comparison works."""
        config1 = MechanismConfig.only_bureaucracy()
        config2 = MechanismConfig.only_bureaucracy()
        config3 = MechanismConfig.only_learning()
        
        assert config1 == config2, "Identical configs should be equal"
        assert config1 != config3, "Different configs should not be equal"
    
    def test_is_baseline_helper(self):
        """Test is_baseline() helper method."""
        assert MechanismConfig.baseline().is_baseline() == True
        assert MechanismConfig.full_model().is_baseline() == False
        assert MechanismConfig.only_bureaucracy().is_baseline() == False
    
    def test_is_full_model_helper(self):
        """Test is_full_model() helper method."""
        assert MechanismConfig.full_model().is_full_model() == True
        assert MechanismConfig.baseline().is_full_model() == False
        assert MechanismConfig.only_bureaucracy().is_full_model() == False
    
    def test_repr_baseline(self):
        """Test string representation of baseline."""
        config = MechanismConfig.baseline()
        assert 'baseline' in repr(config).lower()
    
    def test_repr_full_model(self):
        """Test string representation of full model."""
        config = MechanismConfig.full_model()
        assert 'full_model' in repr(config).lower()


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__, '-v'])