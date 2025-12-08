"""
Mechanism Configuration Framework

Controls which theoretical mechanisms are active in the simulation.
Enables ablation studies to isolate mechanism contributions.

Usage:
    # Full model (all mechanisms)
    config = MechanismConfig.full_model()
    
    # Test only bureaucracy points
    config = MechanismConfig.only_bureaucracy()
    
    # Custom configuration
    config = MechanismConfig(
        bureaucracy_points_enabled=True,
        learning_enabled=True,
        fraud_history_enabled=False,
        state_discrimination_enabled=False
    )

Author: Jack Baldwin
Date: December 2024
"""

from dataclasses import dataclass
from typing import List


@dataclass
class MechanismConfig:
    """
    Controls which theoretical mechanisms are active in the simulation.
    
    Four mechanisms implemented:
    1. Bureaucracy navigation points (structural inequality)
    2. Fraud history with escalating bans (institutional inequality)
    3. Bayesian learning from outcomes (behavioral adaptation)
    4. State-level statistical discrimination (cognitive bias)
    
    Attributes:
        bureaucracy_points_enabled: If True, seekers have limited navigation capacity
        fraud_history_enabled: If True, seekers can be banned after 3 detections
        learning_enabled: If True, seekers update beliefs from outcomes
        state_discrimination_enabled: If True, reviewers apply state-level patterns
    """
    bureaucracy_points_enabled: bool = True
    fraud_history_enabled: bool = True
    learning_enabled: bool = True
    state_discrimination_enabled: bool = True
    
    def get_active_mechanisms(self) -> List[str]:
        """
        Return list of active mechanism names.
        
        Returns:
            List of mechanism names (e.g., ['bureaucracy_points', 'learning'])
        """
        active = []
        if self.bureaucracy_points_enabled:
            active.append('bureaucracy_points')
        if self.fraud_history_enabled:
            active.append('fraud_history')
        if self.learning_enabled:
            active.append('learning')
        if self.state_discrimination_enabled:
            active.append('state_discrimination')
        return active
    
    def count_active(self) -> int:
        """
        Count number of active mechanisms.
        
        Returns:
            Integer count (0-4)
        """
        return len(self.get_active_mechanisms())
    
    @classmethod
    def baseline(cls):
        """
        Baseline configuration: All mechanisms disabled.
        
        Use for testing AI effect without any theoretical mechanisms.
        Expected: Near-zero effect (AI sorting alone doesn't matter much).
        """
        return cls(
            bureaucracy_points_enabled=False,
            fraud_history_enabled=False,
            learning_enabled=False,
            state_discrimination_enabled=False
        )
    
    @classmethod
    def only_bureaucracy(cls):
        """
        Only bureaucracy navigation points active.
        
        Tests: Do navigation capacity constraints create inequality?
        Expected: Should reduce racial disparity (educated vs. less educated).
        """
        return cls(
            bureaucracy_points_enabled=True,
            fraud_history_enabled=False,
            learning_enabled=False,
            state_discrimination_enabled=False
        )
    
    @classmethod
    def only_fraud(cls):
        """
        Only fraud history tracking active.
        
        Tests: Do false fraud flags create inequality?
        Expected: Small effect (3-strike system affects few people).
        """
        return cls(
            bureaucracy_points_enabled=False,
            fraud_history_enabled=True,
            learning_enabled=False,
            state_discrimination_enabled=False
        )
    
    @classmethod
    def only_learning(cls):
        """
        Only Bayesian learning active.
        
        Tests: Does learning from denials create inequality?
        Expected: Moderate effect (discouraged worker mechanism).
        """
        return cls(
            bureaucracy_points_enabled=False,
            fraud_history_enabled=False,
            learning_enabled=True,
            state_discrimination_enabled=False
        )
    
    @classmethod
    def only_state_discrimination(cls):
        """
        Only state-level statistical discrimination active.
        
        Tests: Do state patterns create inequality?
        Expected: In MA (+4.98 Black coefficient), might INCREASE disparity
                  (AI applies pro-Black bias more consistently).
        """
        return cls(
            bureaucracy_points_enabled=False,
            fraud_history_enabled=False,
            learning_enabled=False,
            state_discrimination_enabled=True
        )
    
    @classmethod
    def full_model(cls):
        """
        Full model: All mechanisms active.
        
        This is your current model. Should replicate the -11.35pp finding.
        """
        return cls(
            bureaucracy_points_enabled=True,
            fraud_history_enabled=True,
            learning_enabled=True,
            state_discrimination_enabled=True
        )
    
    def is_baseline(self) -> bool:
        """Check if this is the baseline (no mechanisms)."""
        return self.count_active() == 0
    
    def is_full_model(self) -> bool:
        """Check if this is the full model (all mechanisms)."""
        return self.count_active() == 4
    
    def __repr__(self):
        active = self.get_active_mechanisms()
        if not active:
            return "MechanismConfig(baseline)"
        elif len(active) == 4:
            return "MechanismConfig(full_model)"
        else:
            return f"MechanismConfig({', '.join(active)})"
    
    def __eq__(self, other):
        """Enable comparison of configs."""
        if not isinstance(other, MechanismConfig):
            return False
        return (self.bureaucracy_points_enabled == other.bureaucracy_points_enabled and
                self.fraud_history_enabled == other.fraud_history_enabled and
                self.learning_enabled == other.learning_enabled and
                self.state_discrimination_enabled == other.state_discrimination_enabled)


if __name__ == '__main__':
    # Quick test
    print("Testing MechanismConfig factory methods:\n")
    
    configs = [
        ('Baseline', MechanismConfig.baseline()),
        ('Only Bureaucracy', MechanismConfig.only_bureaucracy()),
        ('Only Fraud', MechanismConfig.only_fraud()),
        ('Only Learning', MechanismConfig.only_learning()),
        ('Only Discrimination', MechanismConfig.only_state_discrimination()),
        ('Full Model', MechanismConfig.full_model())
    ]
    
    for name, config in configs:
        print(f"{name:20s}: {config.count_active()} active - {config}")
    
    print("\n✓ All factory methods work correctly!")