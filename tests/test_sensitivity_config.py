"""
Unit Tests for SensitivityConfig

Minimal tests for sensitivity configuration framework.
Since SensitivityConfig is a simple data class, tests focus on:
  - Factory methods produce correct configs
  - Parameter values are stored correctly
  - Config equality works

Run: pytest tests/test_sensitivity_config.py -v

Expected: 8 tests pass
"""

import pytest
import sys
sys.path.insert(0, 'src')

from core.sensitivity_config import SensitivityConfig, PARAMETER_RANGES, get_sensitivity_configs


class TestSensitivityConfig:
    """Test sensitivity configuration framework."""
    
    def test_baseline_has_default_values(self):
        """Baseline should have all default parameter values."""
        config = SensitivityConfig.baseline()
        
        assert config.approval_rate == 0.70
        assert config.learning_rate == 0.30
        assert config.strictness == 0.50
        assert config.application_threshold == 0.25
        assert config.bureaucracy_points_mult == 1.0
        assert config.parameter_name == 'baseline'
    
    def test_vary_approval_rate_changes_only_approval_rate(self):
        """When varying approval_rate, other params stay at baseline."""
        config = SensitivityConfig.vary_approval_rate(0.80)
        
        assert config.approval_rate == 0.80  # Changed
        assert config.parameter_name == 'approval_rate'
        assert config.parameter_value == 0.80
        
        # Others at baseline
        assert config.learning_rate == 0.30
        assert config.strictness == 0.50
        assert config.application_threshold == 0.25
        assert config.bureaucracy_points_mult == 1.0
    
    def test_vary_learning_rate_changes_only_learning_rate(self):
        """When varying learning_rate, other params stay at baseline."""
        config = SensitivityConfig.vary_learning_rate(0.40)
        
        assert config.learning_rate == 0.40  # Changed
        assert config.parameter_name == 'learning_rate'
        assert config.parameter_value == 0.40
        
        # Others at baseline
        assert config.approval_rate == 0.70
        assert config.strictness == 0.50
    
    def test_vary_strictness(self):
        """Test varying strictness."""
        config = SensitivityConfig.vary_strictness(0.70)
        
        assert config.strictness == 0.70
        assert config.parameter_name == 'strictness'
        assert config.approval_rate == 0.70  # Baseline
    
    def test_vary_application_threshold(self):
        """Test varying application threshold."""
        config = SensitivityConfig.vary_application_threshold(0.30)
        
        assert config.application_threshold == 0.30
        assert config.parameter_name == 'application_threshold'
    
    def test_vary_bureaucracy_mult(self):
        """Test varying bureaucracy multiplier."""
        config = SensitivityConfig.vary_bureaucracy_mult(1.50)
        
        assert config.bureaucracy_points_mult == 1.50
        assert config.parameter_name == 'bureaucracy_mult'
    
    def test_config_equality(self):
        """Test that config equality works."""
        config1 = SensitivityConfig.vary_approval_rate(0.75)
        config2 = SensitivityConfig.vary_approval_rate(0.75)
        config3 = SensitivityConfig.vary_approval_rate(0.80)
        
        assert config1 == config2  # Same params
        assert config1 != config3  # Different values
    
    def test_get_sensitivity_configs_priority1(self):
        """Test generating Priority 1 configs."""
        configs = get_sensitivity_configs(priority=1)
        
        # Should have: 5 approval_rate + 5 learning_rate = 10 configs
        assert len(configs) == 10
        
        # Check they're tuples of (name, config)
        assert all(isinstance(c, tuple) for c in configs)
        assert all(len(c) == 2 for c in configs)
        assert all(isinstance(c[1], SensitivityConfig) for c in configs)
    
    def test_get_sensitivity_configs_priority2(self):
        """Test generating Priority 2 configs."""
        configs = get_sensitivity_configs(priority=2)
        
        # Should have: 5 approval + 5 learning + 5 strictness + 5 threshold = 20
        assert len(configs) == 20
    
    def test_get_sensitivity_configs_priority3(self):
        """Test generating all configs."""
        configs = get_sensitivity_configs(priority=3)
        
        # Should have all 5 parameters × 5 values = 25
        assert len(configs) == 25
    
    def test_parameter_ranges_are_valid(self):
        """Test that PARAMETER_RANGES contains valid ranges."""
        assert 'approval_rate' in PARAMETER_RANGES
        assert 'learning_rate' in PARAMETER_RANGES
        
        # All ranges should be lists with 5 values
        for param, values in PARAMETER_RANGES.items():
            assert isinstance(values, list)
            assert len(values) == 5
            
            # Values should be in ascending order
            assert values == sorted(values)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])