"""
Sensitivity Configuration Framework

Controls parameter values for sensitivity analysis experiments.

Usage:
    # Baseline (current model)
    config = SensitivityConfig.baseline()
    
    # Vary approval rate
    config = SensitivityConfig.vary_approval_rate(0.75)
    
    # Vary learning rate
    config = SensitivityConfig.vary_learning_rate(0.40)
    
    # Custom
    config = SensitivityConfig(
        parameter_name='approval_rate',
        parameter_value=0.75,
        approval_rate=0.75,
        learning_rate=0.30,  # Keep at baseline
        strictness=0.50  # Keep at baseline
    )

Author: Jack Baldwin
Date: December 2024
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SensitivityConfig:
    """
    Configuration for sensitivity analysis experiments.
    
    Stores all parameter values. When varying one parameter, others
    stay at baseline values.
    
    Attributes:
        parameter_name: Which parameter is being varied
        parameter_value: The value being tested
        approval_rate: Baseline approval probability (0.60-0.80)
        learning_rate: Bayesian learning rate (0.10-0.50)
        strictness: Evaluator strictness threshold (0.30-0.70)
        application_threshold: Min probability to apply (0.15-0.35)
        bureaucracy_points_mult: Multiplier for navigation points (0.5-1.5)
    """
    parameter_name: str
    parameter_value: float
    
    # Core parameters with baseline defaults
    approval_rate: float = 0.70
    learning_rate: float = 0.30
    strictness: float = 0.50
    application_threshold: float = 0.25
    bureaucracy_points_mult: float = 1.0
    
    @classmethod
    def baseline(cls):
        """
        Default parameter values (your current model).
        
        Returns:
            SensitivityConfig with all baseline values
        """
        return cls(
            parameter_name='baseline',
            parameter_value=1.0,
            approval_rate=0.70,
            learning_rate=0.30,
            strictness=0.50,
            application_threshold=0.25,
            bureaucracy_points_mult=1.0
        )
    
    @classmethod
    def vary_approval_rate(cls, value):
        """
        Vary approval_rate while keeping others at baseline.
        
        Args:
            value: New approval rate (0.60-0.80 recommended)
        """
        config = cls.baseline()
        config.parameter_name = 'approval_rate'
        config.parameter_value = value
        config.approval_rate = value
        return config
    
    @classmethod
    def vary_learning_rate(cls, value):
        """
        Vary learning_rate while keeping others at baseline.
        
        Args:
            value: New learning rate (0.10-0.50 recommended)
        """
        config = cls.baseline()
        config.parameter_name = 'learning_rate'
        config.parameter_value = value
        config.learning_rate = value
        return config
    
    @classmethod
    def vary_strictness(cls, value):
        """
        Vary strictness while keeping others at baseline.
        
        Args:
            value: New strictness (0.30-0.70 recommended)
        """
        config = cls.baseline()
        config.parameter_name = 'strictness'
        config.parameter_value = value
        config.strictness = value
        return config
    
    @classmethod
    def vary_application_threshold(cls, value):
        """
        Vary application_threshold while keeping others at baseline.
        
        Args:
            value: New threshold (0.15-0.35 recommended)
        """
        config = cls.baseline()
        config.parameter_name = 'application_threshold'
        config.parameter_value = value
        config.application_threshold = value
        return config
    
    @classmethod
    def vary_bureaucracy_mult(cls, value):
        """
        Vary bureaucracy_points_mult while keeping others at baseline.
        
        Args:
            value: New multiplier (0.5-1.5 recommended)
        """
        config = cls.baseline()
        config.parameter_name = 'bureaucracy_mult'
        config.parameter_value = value
        config.bureaucracy_points_mult = value
        return config
    
    def get_config_dict(self):
        """Return configuration as dictionary."""
        return {
            'parameter_name': self.parameter_name,
            'parameter_value': self.parameter_value,
            'approval_rate': self.approval_rate,
            'learning_rate': self.learning_rate,
            'strictness': self.strictness,
            'application_threshold': self.application_threshold,
            'bureaucracy_points_mult': self.bureaucracy_points_mult
        }
    
    def __repr__(self):
        if self.parameter_name == 'baseline':
            return "SensitivityConfig(baseline)"
        return f"SensitivityConfig({self.parameter_name}={self.parameter_value})"
    
    def __eq__(self, other):
        """Enable comparison."""
        if not isinstance(other, SensitivityConfig):
            return False
        return self.get_config_dict() == other.get_config_dict()


# Standard parameter ranges for sensitivity analysis
PARAMETER_RANGES = {
    'approval_rate': [0.60, 0.65, 0.70, 0.75, 0.80],
    'learning_rate': [0.10, 0.20, 0.30, 0.40, 0.50],
    'strictness': [0.30, 0.40, 0.50, 0.60, 0.70],
    'application_threshold': [0.15, 0.20, 0.25, 0.30, 0.35],
    'bureaucracy_mult': [0.50, 0.75, 1.00, 1.25, 1.50],
}


def get_sensitivity_configs(priority=1):
    """
    Generate all sensitivity configurations for a given priority level.
    
    Args:
        priority: 1 (core params), 2 (+ secondary), 3 (all params)
        
    Returns:
        list of (name, config) tuples
    """
    configs = []
    
    # Priority 1: Core assumptions (MUST TEST)
    if priority >= 1:
        for val in PARAMETER_RANGES['approval_rate']:
            configs.append((
                f'approval_rate={val}',
                SensitivityConfig.vary_approval_rate(val)
            ))
        
        for val in PARAMETER_RANGES['learning_rate']:
            configs.append((
                f'learning_rate={val}',
                SensitivityConfig.vary_learning_rate(val)
            ))
    
    # Priority 2: Secondary params (SHOULD TEST)
    if priority >= 2:
        for val in PARAMETER_RANGES['strictness']:
            configs.append((
                f'strictness={val}',
                SensitivityConfig.vary_strictness(val)
            ))
        
        for val in PARAMETER_RANGES['application_threshold']:
            configs.append((
                f'threshold={val}',
                SensitivityConfig.vary_application_threshold(val)
            ))
    
    # Priority 3: All params (NICE TO HAVE)
    if priority >= 3:
        for val in PARAMETER_RANGES['bureaucracy_mult']:
            configs.append((
                f'bureaucracy_mult={val}',
                SensitivityConfig.vary_bureaucracy_mult(val)
            ))
    
    return configs


if __name__ == '__main__':
    # Test the configuration system
    print("Testing SensitivityConfig:")
    print()
    
    configs = [
        ('Baseline', SensitivityConfig.baseline()),
        ('High Approval', SensitivityConfig.vary_approval_rate(0.80)),
        ('Low Learning', SensitivityConfig.vary_learning_rate(0.10)),
        ('Strict', SensitivityConfig.vary_strictness(0.70)),
    ]
    
    for name, config in configs:
        print(f"{name:20s}: {config}")
        print(f"  approval_rate={config.approval_rate}, learning_rate={config.learning_rate}")
        print()
    
    print("Priority 1 configurations:")
    p1_configs = get_sensitivity_configs(priority=1)
    print(f"  {len(p1_configs)} experiments")
    
    print("\nPriority 1+2 configurations:")
    p2_configs = get_sensitivity_configs(priority=2)
    print(f"  {len(p2_configs)} experiments")
    
    print("\n✓ SensitivityConfig working correctly!")